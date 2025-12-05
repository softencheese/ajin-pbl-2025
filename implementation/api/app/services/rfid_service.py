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


class RFIDService:
    def __init__(self, db: Session):
        self.db = db
        self.state_machine = StateMachine()
    
    def process_scan(self, event: ScanEvent) -> ScanResponse:
        """RFID 스캔 이벤트 처리"""
        
        # 1. 포트로 공정/위치 조회
        location = self.db.query(RFIDReaderLocation).filter(
            RFIDReaderLocation.port_name == event.port_name,
            RFIDReaderLocation.is_active == True
        ).first()
        
        if not location:
            return ScanResponse(
                success=False,
                error=ScanError(
                    type="UNKNOWN_PORT",
                    message=f"등록되지 않은 리더기 포트: {event.port_name}"
                ),
                feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
            )
        
        # 1.1 공정 매핑 확인 (자동 등록 후 미설정 상태)
        if location.process_id is None or location.location_type is None:
            return ScanResponse(
                success=False,
                error=ScanError(
                    type="READER_NOT_CONFIGURED",
                    message=f"리더기가 공정에 매핑되지 않았습니다: {event.port_name}. 관리자에게 문의하세요."
                ),
                feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
            )
        
        # 2. EPC로 팔레트 조회
        pallet = self.db.query(Pallet).filter(
            Pallet.rfid_epc == event.epc
        ).first()
        
        if not pallet:
            return ScanResponse(
                success=False,
                error=ScanError(
                    type="PALLET_NOT_FOUND",
                    message=f"등록되지 않은 팔레트: {event.epc}"
                ),
                feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
            )
        
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
            is_final_product=self._is_final_product(pallet)
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
                assembly_lot_id=pallet.assembly_lot_id,
                process_id=location.process_id,
                location_type=location.location_type,
                previous_status=previous_status,
                current_status=next_status,
                event_type="TAG_SCAN",
                event_time=event.scan_time,
                worker_name="System"  # TODO: 작업자 식별
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
                pallet_info.lot_no = pallet.lot.lot_no
                pallet_info.part_number = pallet.lot.part.part_number
                pallet_info.part_name = pallet.lot.part.part_name
            elif pallet.assembly_lot:
                pallet_info.lot_no = pallet.assembly_lot.lot_no
                pallet_info.part_number = pallet.assembly_lot.part.part_number
                pallet_info.part_name = pallet.assembly_lot.part.part_name
            
            # 피드백 결정
            if fifo_warning:
                feedback = Feedback(action="BUZZER", pattern="WARNING", count=3, led_color="YELLOW")
            else:
                feedback = Feedback(action="BUZZER", pattern="SUCCESS", count=1, led_color="GREEN")
            
            return ScanResponse(
                success=True,
                pallet=pallet_info,
                warning=fifo_warning,
                feedback=feedback
            )
        
        except Exception as e:
            self.db.rollback()
            print(f"Error processing scan: {e}")
            return ScanResponse(
                success=False,
                error=ScanError(
                    type="SYSTEM_ERROR",
                    message=str(e)
                ),
                feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
            )
    
    def _validate_wrong_part(self, pallet: Pallet, location: RFIDReaderLocation) -> ScanError | None:
        """오투입 검증 - 품번이 해당 공정에서 처리 가능한지 확인"""
        # TODO: 공정별 허용 품번 테이블과 연동하여 실제 검증 구현
        # 현재는 기본 구현만
        return None
    
    def _validate_fifo(self, pallet: Pallet, location: RFIDReaderLocation) -> FIFOWarning | None:
        """FIFO 검증 - 더 오래된 재고가 있는지 확인"""
        if pallet.status != "Stock" or not pallet.lot:
            return None
        
        # 동일 품번의 더 오래된 Stock 상태 팔레트 조회
        older_stock = self.db.query(Pallet).join(Lot).filter(
            Pallet.status == "Stock",
            Lot.part_id == pallet.lot.part_id,
            Lot.production_date < pallet.lot.production_date,
            Pallet.id != pallet.id
        ).first()
        
        if older_stock:
            days_old = (date.today() - older_stock.lot.production_date).days
            return FIFOWarning(
                type="FIFO_VIOLATION",
                message="더 오래된 재고가 있습니다. 확인 후 진행하세요.",
                oldest_stock={
                    "lot_no": older_stock.lot.lot_no,
                    "production_date": older_stock.lot.production_date.isoformat(),
                    "days_old": days_old
                }
            )
        
        return None
    
    def _is_final_product(self, pallet: Pallet) -> bool:
        """완제품 여부 확인"""
        if pallet.lot and pallet.lot.part:
            return pallet.lot.part.is_final_product
        if pallet.assembly_lot and pallet.assembly_lot.part:
            return pallet.assembly_lot.part.is_final_product
        return False
    
    def update_reader_status(self, event: ReaderStatusEvent) -> ReaderStatusResponse:
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
        
        # TODO: 리더기 상태 로그 테이블에 기록
        # TODO: WebSocket으로 실시간 모니터링 화면에 업데이트
        
        return ReaderStatusResponse(
            success=True,
            message="Status updated"
        )
