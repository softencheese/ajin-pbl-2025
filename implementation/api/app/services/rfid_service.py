from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.pallet import Pallet, PalletHistory
from app.models.physical_pallet import PhysicalPallet
from app.models.rfid import RFIDReaderLocation
from app.models.lot import Lot
from app.models.process import Process
from app.services.state_machine import StateMachine
from app.schemas.rfid import (
    ScanEvent, 
    BarcodeScanEvent,
    ScanResponse, 
    Feedback, 
    PalletInfo,
    ScanError,
    FIFOWarning,
    ReaderStatusEvent,
    ReaderStatusResponse
)
from datetime import datetime, date
from app.core.socket import sio_server # Socket.IO 서버 임포트


class RFIDService:
    def __init__(self, db: Session):
        self.db = db
        self.state_machine = StateMachine()
    
    async def process_barcode_scan(self, event: BarcodeScanEvent) -> ScanResponse:
        """바코드 스캔 이벤트 처리"""
        # 1. 포트로 공정/위치 조회
        location = self._get_reader_location(event.port_name)
        if isinstance(location, ScanResponse):
            await self._emit_scan_error('UNKNOWN_PORT', event.port_name, event.barcode, location.error.message)
            return location

        if location.process_id is None or location.location_type is None:
            error_response = self._create_error_response('READER_NOT_CONFIGURED', f"리더기 설정 오류: {event.port_name}")
            await self._emit_scan_error('READER_NOT_CONFIGURED', event.port_name, event.barcode, error_response.error.message)
            return error_response

        # 2. Barcode로 팔레트 조회 (Locking)
        # Barcode -> Lot -> Pallet
        # Lot.barcode가 event.barcode와 일치하는 것을 찾고, 그 Lot에 연결된 Pallet를 찾음
        
        # 2.1 Lot 조회
        lot = self.db.query(Lot).filter(Lot.barcode == event.barcode).first()
        if not lot:
             # LOT이 없으면 팔레트도 찾을 수 없음
             return await self._handle_pallet_not_found(event.port_name, event.barcode, "BARCODE_NOT_FOUND")

        # 2.2 Pallet 조회 (Locking)
        pallet = self.db.query(Pallet).filter(
            Pallet.lot_id == lot.id
        ).with_for_update().first()
        
        if not pallet:
             return await self._handle_pallet_not_found(event.port_name, event.barcode, "PALLET_NOT_LINKED")

        # 3. 공통 로직 실행
        return await self._process_pallet_event(pallet, location, event.scan_time, event.barcode, "BARCODE")

    async def process_scan(self, event: ScanEvent) -> ScanResponse:
        """RFID 스캔 이벤트 처리"""
        
        # 1. 포트로 공정/위치 조회
        location = self._get_reader_location(event.port_name)
        if isinstance(location, ScanResponse):
            await self._emit_scan_error('UNKNOWN_PORT', event.port_name, event.epc, location.error.message)
            return location
        
        # 1.1 공정 매핑 확인
        if location.process_id is None or location.location_type is None:
            error_response = self._create_error_response('READER_NOT_CONFIGURED', f"리더기 설정 오류: {event.port_name}")
            await self._emit_scan_error('READER_NOT_CONFIGURED', event.port_name, event.epc, error_response.error.message)
            return error_response
        
        # 2. EPC로 팔레트 조회 (Locking)
        pallet = self.db.query(Pallet).join(
            PhysicalPallet, Pallet.physical_pallet_id == PhysicalPallet.id
        ).filter(
            PhysicalPallet.epc == event.epc
        ).with_for_update().first()
        
        if not pallet:
            # 2.1 자동 바인딩 시도 (생산 공정 OUT 위치에서만)
            if location.location_type == "OUT":
                pallet = await self._try_auto_bind_pallet(event.epc, location)
                if not pallet:
                    return await self._handle_pallet_not_found(event.port_name, event.epc, "PALLET_NOT_FOUND (AUTO_BIND_FAILED)")
            else:
                return await self._handle_pallet_not_found(event.port_name, event.epc, "PALLET_NOT_FOUND")
        
        # 3. 공통 로직 실행
        return await self._process_pallet_event(pallet, location, event.scan_time, event.epc, "RFID")

    async def _try_auto_bind_pallet(self, epc: str, location: RFIDReaderLocation) -> Pallet | None:
        """가상 팔레트와 실물 태그 자동 바인딩 시도 (OUT 위치)"""
        try:
            # 1. PhysicalPallet 조회 또는 생성
            physical_pallet = self.db.query(PhysicalPallet).filter(
                PhysicalPallet.epc == epc
            ).first()
            
            if not physical_pallet:
                # physical_pallet.py의 status는 Enum이지만 rfid_service에서는 문자열 사용 추세
                # 모델 정의에 맞춰 문자열 보냄 (SQLAlchemy가 Enum으로 변환 처리)
                physical_pallet = PhysicalPallet(
                    epc=epc,
                    pallet_code=f"P-{epc[-6:]}" if len(epc) >= 6 else epc,
                    status="Empty"
                )
                self.db.add(physical_pallet)
                self.db.flush() # ID 획득을 위해 flush
                print(f"  [AUTO_BIND] Created new PhysicalPallet for EPC: {epc}")
            elif physical_pallet.status == "Stock":
                 # 이미 생산 완료되어 재고인 팔레트가 미연결 상태로 돌아다니는 경우 (드문 케이스)
                 # 여기서는 무시하거나 에러 처리 가능. 현재는 그냥 생성 로직으로 간다.
                 pass

            # 2. 해당 공정에 할당된 가상 팔레트 중 실물이 아직 연결되지 않은 것 찾기
            # status가 'Generated' 또는 'Empty'인 것 중 가장 오래된 것 (ID순)
            pallet = self.db.query(Pallet).filter(
                Pallet.current_process_id == location.process_id,
                Pallet.physical_pallet_id == None,
                # Pallet status 필드는 문자열
                Pallet.status.in_(["Generated", "Empty"])
            ).order_by(Pallet.id.asc()).with_for_update().first()
            
            if pallet:
                # 3. 바인딩
                pallet.physical_pallet_id = physical_pallet.id
                pallet.tag_status = 'IN_USE'
                pallet.tag_registered_at = datetime.now()
                # physical_pallet 상태도 Producing으로 변경 (이후 _process_pallet_event에서도 변경되지만 미리 선언)
                physical_pallet.status = "Producing"
                
                print(f"  [AUTO_BIND] Bound EPC {epc} to Pallet {pallet.pallet_no} (LOT: {pallet.lot_id})")
                return pallet
            
            print(f"  [AUTO_BIND] No candidate virtual pallet found for process_id: {location.process_id}")
            return None
        except Exception as e:
            print(f"  [AUTO_BIND] Error during auto-binding: {type(e).__name__}: {e}")
            return None

    async def _process_pallet_event(self, pallet: Pallet, location: RFIDReaderLocation, scan_time: datetime, identifier: str, scan_type: str) -> ScanResponse:
        """팔레트 이벤트 처리 공통 로직 (RFID/Barcode)"""
        try:
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

            # Deregistered로 상태 전이 시 LOT 연결 해제는 트랜잭션 마지막에 수행
            # (LOT 상태 연동 로직에서 현재 LOT의 다른 팔레트들을 조회해야 하므로)
            if next_status == "Deregistered":
                # pallet.lot_id = None  <-- 이 시점에는 유지
                pass
            
            # Deregistered 상태가 Generated로 상태 전이시 LOT 연결
            # if previous_status == "Deregistered" and next_status == "Generated":
            #     # 빈 팔레트용 LOT 자동 생성 및 연결
            #     new_lot = Lot(
            #         lot_number=f"LOT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{pallet.id}",
            #         item_id=None,
            #         quantity=0,
            #         created_at=datetime.now()
            #     )
            #     self.db.add(new_lot)
            #     self.db.commit()
            #     self.db.refresh(new_lot)
                
            #     pallet.lot_id = new_lot.id
            
            
            # 5. 트랜잭션 처리
            # 상태 업데이트 (pallet.status가 상태 전이 기준이 됨, physical_pallet도 동기화)
            pallet.status = next_status
            pallet.current_process_id = location.process_id
            if pallet.physical_pallet:
                pallet.physical_pallet.status = next_status

            # LOT 상태 연동 로직
            if pallet.lot:
                lot = pallet.lot
                
                # 1. 생산/소비 시작 시 LOT 상태를 PROCESS로 변경
                if next_status in ["Consuming", "Producing"] and lot.status in ["WAIT", "STOCK"]:
                    lot.status = "PROCESS"
                    print(f"  [LOT_SYNC] LOT {lot.lot_number} status: {lot.status} (by Pallet {pallet.pallet_no})")

                # 2. 모든 팔레트가 완료/회수되었는지 확인하여 LOT 상태 최종 업데이트
                # 현재 LOT에 연결된 모든 팔레트 조회
                all_pallets = self.db.query(Pallet).filter(Pallet.lot_id == lot.id).all()
                
                if next_status in ["Stock", "Finished"]:
                    # 생산 완료 체크: 모든 팔레트가 Stock, Finished, Hold, Defect 중 하나인지 확인
                    is_all_done = all(p.status in ["Stock", "Finished", "Hold", "Defect"] for p in all_pallets)
                    if is_all_done:
                        lot.status = "STOCK"
                        print(f"  [LOT_SYNC] LOT {lot.lot_number} status: STOCK (All pallets done)")

                elif next_status == "Deregistered":
                    # 소비 완료 체크: 모든 팔레트가 Deregistered(또는 곧 될 예정)인지 확인
                    # 현재 스캔된 팔레트(pallet)는 아직 DB상으로는 이전 상태일 수 있으므로 next_status 고려
                    is_all_consumed = True
                    for p in all_pallets:
                        p_status = next_status if p.id == pallet.id else p.status
                        if p_status != "Deregistered":
                            is_all_consumed = False
                            break
                    
                    if is_all_consumed:
                        lot.status = "CONSUMED"
                        print(f"  [LOT_SYNC] LOT {lot.lot_number} status: CONSUMED (All pallets deregistered)")

                    # 이제 LOT 연결 해제
                    pallet.lot_id = None
            
            # 리더기 마지막 스캔 시간 갱신
            location.last_scan_time = scan_time
            
            # 이력 기록
            notes = None
            if fifo_warning and location.location_type == "IN":
                oldest = fifo_warning.oldest_stock
                notes = f"FIFO 위반: {oldest.get('pallet_no', 'N/A')} (생성일: {oldest.get('created_at', 'N/A')}) 먼저 출고 필요"

            history = PalletHistory(
                pallet_id=pallet.id,
                lot_id=pallet.lot_id, # pallet original lot_id (next_status=Deregistered 시 위에서 None 됨)
                process_id=location.process_id,
                location_type=location.location_type,
                reader_location_id=location.id,
                previous_status=previous_status,
                new_status=next_status,
                event_type=f"{scan_type}_SCAN",
                scan_time=scan_time,
                worker_name="System",
                notes=notes
            )
            self.db.add(history)
            
            # Deregistered 처리를 이력 기록 후에 수행 (이력에는 lot_id 남기기 위해)
            # --> 위에서 이미 pallet.lot_id = None 으로 변경했으나, DB commit 전이므로 history에는 pallet.lot_id 전송됨
            
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
                if pallet.lot.item:
                    pallet_info.part_number = pallet.lot.item.item_code
                    pallet_info.part_name = pallet.lot.item.item_name
            
            # 피드백 결정
            if fifo_warning:
                feedback = Feedback(action="BUZZER", pattern="WARNING", count=3, led_color="YELLOW")
            else:
                feedback = Feedback(action="BUZZER", pattern="SUCCESS", count=1, led_color="GREEN")
            
            # Socket.IO 이벤트 발송
            await sio_server.emit('scan_event', {
                'type': scan_type,
                'pbl_location': location.location_type,
                'process_code': location.process.process_code if location.process else 'UNKNOWN',
                'scan_time': scan_time.isoformat(),
                'pallet_no': pallet.pallet_no,
                "status": next_status,
                "identifier": identifier, # EPC or Barcode
                "port_name": location.port_name,
                "success": True
            })

            # FIFO 전용 이벤트 발송 (IN 위치에서만, Stock 팔레트를 스캔한 경우)
            if location.location_type == "IN" and previous_status == "Stock":
                await sio_server.emit('fifo_scan', {
                    'pallet_id': pallet.id,
                    'pallet_no': pallet.pallet_no,
                    'lot_no': pallet.lot.lot_number if pallet.lot else None,
                    'scan_time': scan_time.isoformat(),
                    'is_violation': fifo_warning is not None,
                    'status': 'VIOLATION' if fifo_warning else 'OK'
                })

            return ScanResponse(
                success=True,
                pallet=pallet_info,
                warning=fifo_warning,
                feedback=feedback
            )

        except Exception as e:
            self.db.rollback()
            print(f"[SYSTEM_ERROR] _process_pallet_event: {type(e).__name__}: {e}")
            return self._create_error_response("SYSTEM_ERROR", "시스템 오류가 발생했습니다.")

    def _get_reader_location(self, port_name: str) -> RFIDReaderLocation | ScanResponse:
        location = self.db.query(RFIDReaderLocation).filter(
            RFIDReaderLocation.port_name == port_name,
            RFIDReaderLocation.is_active == True
        ).first()
        
        if not location:
             error_response = self._create_error_response("UNKNOWN_PORT", f"등록되지 않은 리더기 포트: {port_name}")
             return error_response
        return location

    def _create_error_response(self, error_type: str, message: str) -> ScanResponse:
        return ScanResponse(
            success=False,
            error=ScanError(type=error_type, message=message),
            feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
        )

    async def _emit_scan_error(self, type: str, port_name: str, identifier: str, message: str):
        await sio_server.emit('scan_error', {
            'type': type,
            'port_name': port_name,
            'identifier': identifier,
            'message': message
        })

    async def _handle_pallet_not_found(self, port_name: str, identifier: str, error_type: str) -> ScanResponse:
         error_response = self._create_error_response(error_type, f"대상을 찾을 수 없습니다: {identifier}")
         await self._emit_scan_error(error_type, port_name, identifier, error_response.error.message)
         return error_response

    
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
        """FIFO 검증 - 전체 팔레트 기준으로 더 오래된 재고가 있는지 확인"""
        if pallet.status != "Stock":
            return None

        # 전체 Stock 상태 팔레트 중 더 오래된 것 조회 (품목 구분 없음)
        # created_at이 같으면 ID가 작은 것이 먼저 생성된 것으로 간주
        older_stock = self.db.query(Pallet).filter(
            Pallet.status == "Stock",
            Pallet.id != pallet.id
        ).filter(
            (Pallet.created_at < pallet.created_at) |
            ((Pallet.created_at == pallet.created_at) & (Pallet.id < pallet.id))
        ).order_by(Pallet.created_at.asc(), Pallet.id.asc()).first()

        if older_stock:
            days_old = (datetime.now() - older_stock.created_at).days
            return FIFOWarning(
                type="FIFO_VIOLATION",
                message="더 오래된 재고가 있습니다. 확인 후 진행하세요.",
                oldest_stock={
                    "pallet_no": older_stock.pallet_no,
                    "lot_no": older_stock.lot.lot_number if older_stock.lot else None,
                    "created_at": older_stock.created_at.isoformat(),
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
