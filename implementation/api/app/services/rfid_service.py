from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.pallet import Pallet, PalletHistory
from app.models.rfid import RFIDReaderLocation
from app.models.lot import Lot
from app.models.process import Process
from app.services.state_machine import StateMachine
from app.schemas.rfid import (
    ScanEvent, 
    ScanResponse, 
    Feedback, 
    PalletInfo,
    ScanError,
    FIFOWarning,
    ReaderStatusEvent,
    ReaderStatusResponse
)
from datetime import datetime, date
from app.sio import sio_server # Socket.IO 서버 임포트


class RFIDService:
    def __init__(self, db: Session):
        self.db = db
        self.state_machine = StateMachine()
    
    async def process_scan(self, event: ScanEvent) -> ScanResponse:
        """RFID 스캔 이벤트 처리"""
        
        # 1. 포트로 공정/위치 조회
        location = self.db.query(RFIDReaderLocation).filter(
            RFIDReaderLocation.port_name == event.port_name,
            RFIDReaderLocation.is_active == True
        ).first()
        
        if not location:
            error_response = ScanResponse(
                success=False,
                error=ScanError(
                    type="UNKNOWN_PORT",
                    message=f"등록되지 않은 리더기 포트: {event.port_name}"
                ),
                feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
            )
            # WebSocket 에러 이벤트 발송
            await sio_server.emit('scan_error', {
                'type': 'UNKNOWN_PORT',
                'port_name': event.port_name,
                'epc': event.epc,
                'message': error_response.error.message
            })
            return error_response
        
        # 1.1 공정 매핑 확인 (자동 등록 후 미설정 상태)
        if location.process_id is None or location.location_type is None:
            error_response = ScanResponse(
                success=False,
                error=ScanError(
                    type="READER_NOT_CONFIGURED",
                    message=f"리더기가 공정에 매핑되지 않았습니다: {event.port_name}. 관리자에게 문의하세요."
                ),
                feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
            )
            await sio_server.emit('scan_error', {
                'type': 'READER_NOT_CONFIGURED',
                'port_name': event.port_name,
                'epc': event.epc,
                'message': error_response.error.message
            })
            return error_response
        
        # 2. EPC로 팔레트 조회
        pallet = self.db.query(Pallet).filter(
            Pallet.rfid_epc == event.epc
        ).first()
        
        if not pallet:
            error_response = ScanResponse(
                success=False,
                error=ScanError(
                    type="PALLET_NOT_FOUND",
                    message=f"등록되지 않은 팔레트: {event.epc}"
                ),
                feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
            )
            await sio_server.emit('scan_error', {
                'type': 'PALLET_NOT_FOUND',
                'port_name': event.port_name,
                'epc': event.epc,
                'message': error_response.error.message
            })
            return error_response
        
        # 3. 검증 로직 실행
        # 3.1 오투입 검증 (IN 위치에서만)
        if location.location_type == "IN":
            wrong_part_error = self._validate_wrong_part(pallet, location)
            if wrong_part_error:
                return ScanResponse(
                    success=False,
                    error=wrong_part_error,
                    feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
                )
            
            # 3.2 FIFO 검증
            fifo_warning = self._validate_fifo(pallet, location)
        else:
            fifo_warning = None
        
        # 4. 상태 전이 결정
        previous_status = pallet.status
        transition_result = self.state_machine.get_next_state(
            current_status=previous_status,
            process_code=location.process.process_code,
            location_type=location.location_type,
            is_final_product=self._is_final_product(pallet),
            is_first_process=getattr(location.process, 'is_first_process', False)
        )
        
        if not transition_result["allowed"]:
            return ScanResponse(
                success=False,
                error=ScanError(
                    type="INVALID_TRANSITION",
                    message=transition_result["message"],
                    details={
                        "current_status": previous_status,
                        "location_type": location.location_type
                    }
                ),
                feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
            )
        
        next_status = transition_result["next_status"]
        
        # Hold 해제 시 이전 상태 복구
        if next_status == "__RESTORE_PRE_HOLD__":
            next_status = self._get_pre_hold_status(pallet.id)
        
        # 5. 트랜잭션 처리
        try:
            # 상태 업데이트
            pallet.status = next_status
            pallet.current_process_id = location.process_id
            
            # 리더기 마지막 스캔 시간 갱신 (대시보드 조회용)
            location.last_scan_time = event.scan_time
            
            # 이력 기록
            notes = None
            if fifo_warning:
                notes = f"FIFO 경고: {fifo_warning.message}"
            
            history = PalletHistory(
                pallet_id=pallet.id,
                lot_id=pallet.lot_id,
                process_id=location.process_id,
                location_type=location.location_type,
                reader_location_id=location.id,
                previous_status=previous_status,
                new_status=next_status,
                event_type="TAG_SCAN",
                scan_time=event.scan_time,
                worker_name="System"
            )
            self.db.add(history)
            
            self.db.commit()
            self.db.refresh(pallet)
            
            # 6. 응답 생성
            pallet_info = PalletInfo(
                pallet_no=pallet.pallet_no,
                previous_status=previous_status,
                current_status=next_status
            )
            
            if pallet.lot:
                pallet_info.lot_no = pallet.lot.lot_number
                # part_number, part_name -> item_code, item_name
                if pallet.lot.item:
                    pallet_info.part_number = pallet.lot.item.item_code
                    pallet_info.part_name = pallet.lot.item.item_name
            
            # 피드백 결정
            if fifo_warning:
                feedback = Feedback(action="BUZZER", pattern="WARNING", count=3, led_color="YELLOW")
            else:
                feedback = Feedback(action="BUZZER", pattern="SUCCESS", count=1, led_color="GREEN")
            
            # Socket.IO 이벤트 발송 (return 전에 실행해야 함)
            await sio_server.emit('scan_event', {
                'type': 'SCAN',
                'pbl_location': location.location_type,
                'process_code': location.process.process_code if location.process else 'UNKNOWN',
                'scan_time': event.scan_time.isoformat(),
                'pallet_no': pallet.pallet_no,
                "status": next_status,
                "epc": event.epc,
                "port_name": event.port_name,
                "success": True
            })
            
            return ScanResponse(
                success=True,
                pallet=pallet_info,
                warning=fifo_warning,
                feedback=feedback
            )

        
        except Exception as e:
            self.db.rollback()
            # 에러 로깅 (디버깅용) - 실제 운영에서는 logging 모듈 사용 권장
            print(f"[SYSTEM_ERROR] process_scan: {type(e).__name__}: {e}")
            
            # 내부 에러 메시지 숨기기 (보안)
            return ScanResponse(
                success=False,
                error=ScanError(
                    type="SYSTEM_ERROR",
                    message="시스템 오류가 발생했습니다. 관리자에게 문의하세요."
                ),
                feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
            )
    
    def _validate_wrong_part(self, pallet: Pallet, location: RFIDReaderLocation) -> ScanError | None:
        """오투입 검증 - 품번이 해당 공정에서 처리 가능한지 확인 (DB 기반)"""
        if not pallet.lot or not pallet.lot.item or not location.process:
            return None

        process = location.process
        item_type = pallet.lot.item.item_type
        
        # DB에서 허용 타입 조회 (쉼표로 구분된 문자열)
        allowed_types_str = getattr(process, 'allowed_item_types', None)
        
        if not allowed_types_str:
            # 설정이 없으면 검증 통과 (하위 호환성)
            return None
        
        allowed_types = [t.strip() for t in allowed_types_str.split(',')]
        
        if item_type not in allowed_types:
            return ScanError(
                type="WRONG_PART",
                message=f"오투입 감지: {process.process_code} 공정에는 {allowed_types} 타입만 투입 가능합니다. (현재: {item_type})",
                details={
                    "process_code": process.process_code,
                    "allowed_types": allowed_types,
                    "current_item_type": item_type,
                    "item_code": pallet.lot.item.item_code
                }
            )
            
        return None
    
    def _validate_fifo(self, pallet: Pallet, location: RFIDReaderLocation) -> FIFOWarning | None:
        """FIFO 검증 - 더 오래된 재고가 있는지 확인"""
        if pallet.status != "Stock" or not pallet.lot:
            return None
        
        # 동일 품번의 더 오래된 Stock 상태 팔레트 조회
        # Lot.part_id -> Lot.item_id
        older_stock = self.db.query(Pallet).join(Lot).filter(
            Pallet.status == "Stock",
            Lot.item_id == pallet.lot.item_id,
            Lot.production_date < pallet.lot.production_date,
            Pallet.id != pallet.id
        ).first()
        
        if older_stock:
            days_old = (date.today() - older_stock.lot.production_date).days
            return FIFOWarning(
                type="FIFO_VIOLATION",
                message="더 오래된 재고가 있습니다. 확인 후 진행하세요.",
                oldest_stock={
                    "lot_no": older_stock.lot.lot_number,
                    "production_date": older_stock.lot.production_date.isoformat(),
                    "days_old": days_old
                }
            )
        
        return None
    
    def _get_pre_hold_status(self, pallet_id: int) -> str:
        """Hold 상태 진입 전의 상태를 조회"""
        # Hold 상태로 변경된 가장 최근 이력 조회
        hold_history = self.db.query(PalletHistory).filter(
            PalletHistory.pallet_id == pallet_id,
            PalletHistory.new_status == "Hold"
        ).order_by(PalletHistory.scan_time.desc()).first()
        
        if hold_history and hold_history.previous_status:
            return hold_history.previous_status
        
        # 조회 실패 시 기본값
        return "Stock"
    
    def _is_final_product(self, pallet: Pallet) -> bool:
        """완제품 여부 확인"""
        if pallet.lot and pallet.lot.item:
            return pallet.lot.item.item_type == "PRODUCT"
        return False
    
    async def update_reader_status(self, event: ReaderStatusEvent) -> ReaderStatusResponse:
        """리더기 상태 업데이트"""
        location = self.db.query(RFIDReaderLocation).filter(
            RFIDReaderLocation.port_name == event.port_name
        ).first()
        
        if not location:
            # Auto-register new reader
            location = RFIDReaderLocation(
                port_name=event.port_name,
                process_id=None,
                location_type=None,
                description="Auto-registered",
                is_active=True
            )
            self.db.add(location)
            self.db.commit()
            self.db.refresh(location)
            
            return ReaderStatusResponse(
                success=True,
                message=f"Registered new reader: {event.port_name}"
            )

        
        # WebSocket 이벤트 발송
        await sio_server.emit('reader_status', {
            'port_name': event.port_name,
            'status': event.status,
            'timestamp': datetime.now().isoformat()
        })
        
        return ReaderStatusResponse(
            success=True,
            message="Status updated"
        )
