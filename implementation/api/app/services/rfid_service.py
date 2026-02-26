from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.pallet import Pallet, PalletHistory
from app.models.physical_pallet import PhysicalPallet
from app.models.rfid import RFIDReaderLocation
from app.models.lot import Lot
from app.models.process import Process
from app.models.lot_genealogy import LotGenealogy
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
from app.services.lot_service import sync_lot_status_and_quantity


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

        is_global_reader = location.location_type in ["DEFECT", "DEFECT_OUT", "HOLD", "HOLD_OUT", "SCRAP"]
        if location.location_type is None or (location.process_id is None and not is_global_reader):
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
        # 1) 현재 비어있는(Empty/Generated) 팔레트 중 가장 오래된 것 먼저 (생산 시작용)
        # 2) 만약 없으면, 이미 생산 중이거나 재고인 것 중 가장 최신 것 (상태 전이용)
        pallet = self.db.query(Pallet).filter(
            Pallet.lot_id == lot.id,
            Pallet.status.in_(["Empty", "Generated"])
        ).order_by(Pallet.id.asc()).with_for_update().first()
        
        if not pallet:
            pallet = self.db.query(Pallet).filter(
                Pallet.lot_id == lot.id,
                Pallet.status != "Deregistered"
            ).order_by(Pallet.id.desc()).with_for_update().first()
        
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
        is_global_reader = location.location_type in ["DEFECT", "DEFECT_OUT", "HOLD", "HOLD_OUT", "SCRAP", "SHIPPING"]
        if location.location_type is None or (location.process_id is None and not is_global_reader):
            error_response = self._create_error_response('READER_NOT_CONFIGURED', f"리더기 설정 오류: {event.port_name}")
            await self._emit_scan_error('READER_NOT_CONFIGURED', event.port_name, event.epc, error_response.error.message)
            return error_response
        
        # 2. EPC로 팔레트 조회 (Locking)
        # 최신 팔레트부터 조회
        pallet = self.db.query(Pallet).join(
            PhysicalPallet, Pallet.physical_pallet_id == PhysicalPallet.id
        ).filter(
            PhysicalPallet.epc == event.epc,
            Pallet.status != "Deregistered"  # [Fix] Deregistered된 과거 기록 제외
        ).order_by(Pallet.id.desc()).with_for_update().first()
        
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
                physical_pallet = PhysicalPallet(
                    epc=epc,
                    pallet_code=f"P-{epc[-6:]}" if len(epc) >= 6 else epc
                )
                self.db.add(physical_pallet)
                self.db.flush() # ID 획득을 위해 flush
                print(f"  [AUTO_BIND] Created new PhysicalPallet for EPC: {epc}")

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
            # 3.1 IN 위치: 현재 공정에서 생산 중(Producing)인 팔레트가 있고,
            #     새로운 Stock 팔레트를 투입하려는 경우에만 IN 거부
            #     (이미 Consuming 상태인 팔레트의 회수(Deregistered)는 허용)
            if location.location_type == "IN" and location.process_id and pallet.status == "Stock":
                producing_count = self.db.query(Pallet).filter(
                    Pallet.current_process_id == location.process_id,
                    Pallet.status == "Producing"
                ).count()
                if producing_count > 0:
                    return ScanResponse(
                        success=False,
                        error=ScanError(
                            type="PROCESS_BUSY",
                            message=f"현재 공정에서 생산 중인 팔레트가 있습니다. OUT 적재 완료 후 다시 투입하세요."
                        ),
                        feedback=Feedback(action="BUZZER", pattern="ERROR", count=2, led_color="YELLOW")
                    )

            # 3.2 오투입 검증 (IN 위치에서만)
            if location.location_type == "IN":
                wrong_part_error = self._validate_wrong_part(pallet, location)
                if wrong_part_error:
                    return ScanResponse(
                        success=False,
                        error=wrong_part_error,
                        feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
                    )
                
                # 3.3 FIFO 검증 (1회 차단, 2회째 통과)
                raw_fifo_warning = self._validate_fifo(pallet, location)
                fifo_warning = None
                
                if raw_fifo_warning:
                    # 해당 팔레트가 현재 위치에서 이미 FIFO 위반으로 차단된 기록이 있는지 확인
                    recent_violation = self.db.query(PalletHistory).filter(
                        PalletHistory.pallet_id == pallet.id,
                        PalletHistory.location_type == location.location_type,
                        PalletHistory.event_type == "FIFO_VIOLATION_ATTEMPT"
                    ).order_by(PalletHistory.scan_time.desc()).first()

                    if recent_violation:
                        # 이미 한 번 차단되었으므로 이번에는 통과 (경고 내용은 유지)
                        fifo_warning = raw_fifo_warning
                        # 2회차 통과 알림 발송
                        await sio_server.emit('fifo_scan', {
                            'pallet_id': pallet.id,
                            'pallet_no': pallet.pallet_no,
                            'lot_no': pallet.lot.lot_number if pallet.lot else None,
                            'scan_time': scan_time.isoformat(),
                            'is_violation': True,
                            'status': 'FORCED_PASS'
                        })
                    else:
                        error_msg = raw_fifo_warning.message
                        
                        # FIFO 모니터링 페이지용 이벤트 발송 및 글로벌 알림 트리거
                        await sio_server.emit('fifo_scan', {
                            'pallet_id': pallet.id,
                            'pallet_no': pallet.pallet_no,
                            'lot_no': pallet.lot.lot_number if pallet.lot else None,
                            'scan_time': scan_time.isoformat(),
                            'is_violation': True,
                            'status': 'BLOCKED'
                        })
                        
                        # 차단 이력 기록
                        history = PalletHistory(
                            pallet_id=pallet.id,
                            lot_id=pallet.lot_id,
                            process_id=location.process_id,
                            location_type=location.location_type,
                            reader_location_id=location.id,
                            previous_status=pallet.status,
                            new_status=pallet.status,
                            event_type="FIFO_VIOLATION_ATTEMPT",
                            scan_time=scan_time,
                            worker_name="System",
                            notes=error_msg
                        )
                        self.db.add(history)
                        self.db.commit()
                        
                        return ScanResponse(
                            success=False,
                            error=ScanError(
                                type="FIFO_VIOLATION",
                                message=error_msg,
                                details=raw_fifo_warning.oldest_stock
                            ),
                            feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
                        )
            else:
                fifo_warning = None
            
            # 4. 상태 전이 결정
            previous_status = pallet.status
            
            process_code = location.process.process_code if location.process else None
            is_first_process = getattr(location.process, 'is_first_process', False) if location.process else False
            
            transition_result = self.state_machine.get_next_state(
                current_status=previous_status,
                process_code=process_code,
                location_type=location.location_type,
                is_final_product=self._is_final_product(pallet),
                is_first_process=is_first_process
            )
            
            # [Added] 4.1 생산 공정 투입(Consuming) LOT 검증
            # 첫 공정이 아닌 경우, 생산(Producing/Stock/Finished) 시 반드시 투입된 LOT가 있어야 함
            if location.location_type in ["OUT", "SHIPPING"] and transition_result["allowed"]:
                # 첫 공정 여부 판단 (플래그 또는 공정 순번 1 이하)
                is_first = getattr(location.process, 'is_first_process', False)
                if location.process and not is_first:
                    if (location.process.process_order or 0) <= 1:
                        is_first = True
                
                # [Fix] 생산 시작(Empty -> Producing)시에만 원재료/재공품 투입 여부 확인
                # 이미 Producing 상태인 팔레트가 Stock/Finished로 넘어가는(생산 완료) 것은 막지 않음
                if not is_first and previous_status in ["Empty", "Generated", "Deregistered"]:
                    # 현재 공정에서 소비 중인 다른 팔레트/LOT가 있는지 확인
                    consuming_count = self.db.query(Pallet).filter(
                        Pallet.current_process_id == location.process_id,
                        Pallet.status == "Consuming"
                    ).count()
                    
                    if consuming_count == 0:
                        return ScanResponse(
                            success=False,
                            error=ScanError(
                                type="NO_INPUT_LOT",
                                message=f"[{location.process.process_name}] 투입된 원자재/재공품이 없습니다. 이전 공정 팔레트를 IN 리더기에 먼저 스캔하세요."
                            ),
                            feedback=Feedback(action="BUZZER", pattern="ERROR", count=3, led_color="RED")
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
            
            # Rollback 처리 (Defect/Hold 해제 시 이전 상태 복구)
            if next_status == "Rollback":
                if pallet.previous_status:
                    next_status = pallet.previous_status
                else:
                    next_status = "Stock" # 기본값

            # 상태가 변경될 때 이전 상태를 저장
            if previous_status != next_status and next_status not in ["Rollback", "Scrap"]:
                pallet.previous_status = previous_status
            # (LOT 상태 연동 로직에서 현재 LOT의 다른 팔레트들을 조회해야 하므로)
            if next_status == "Deregistered":
                # pallet.lot_id = None  <-- 이 시점에는 유지
                pass
            
            # 4.2 수량 자동 설정 (생산 시작 시 권장 용량 부여)
            if location.location_type == "OUT" and next_status in ["Producing", "Stock", "Finished"]:
                if (pallet.quantity or 0) == 0 and pallet.lot and pallet.lot.item:
                    pallet.quantity = pallet.lot.item.pallet_capacity or 0
                    print(f"  [QUANTITY] Pre-set pallet {pallet.pallet_no} quantity to {pallet.quantity}")

            # 4.3 실시간 Genealogy (추적성) 처리
            # (A) 원자재/재공품 투입 시작 시 -> 현재 공정의 모든 'Producing' 팔레트와 연결
            if next_status == "Consuming":
                self._handle_consuming_genealogy(pallet, location)
            
            # (B) 공정 완료(생산 시작 또는 완료) 시 -> 현재 공정의 모든 'Consuming' 팔레트와 연결
            if location.location_type == "OUT" and next_status in ["Producing", "Stock", "Finished"]:
                self._handle_production_genealogy(pallet, location, previous_status)

            # 5. 트랜잭션 처리
            # 상태 업데이트 (pallet.status가 상태 전이 기준이 됨, physical_pallet도 동기화)
            pallet.status = next_status
            if location.process_id is not None:
                pallet.current_process_id = location.process_id
            
            # [Added] 생산 수량 누적
            if previous_status == "Producing" and next_status in ["Stock", "Finished"]:
                if pallet.lot:
                    pallet.lot.produced_quantity += (pallet.quantity or 0)
                    self.db.add(pallet.lot)

            # [Added] 소비 완료 시 수량 0 처리
            if previous_status == "Consuming":
                pallet.quantity = 0
            
            # AI_README: 팔레트가 Deregistered 또는 Scrap 시 tag_status 및 실물 상태 업데이트
            elif next_status == "Deregistered":
                pallet.tag_status = "AVAILABLE"
                pallet.tag_deregistered_at = datetime.now()
                pallet.quantity = 0
            elif next_status == "Scrap":
                # AI_README: 폐기 시 생산 수량(produced_quantity)에서 차감하여 Net 생산량을 유지
                if pallet.lot and previous_status in ["Stock", "Finished", "Defect", "Hold"]:
                    pallet.lot.produced_quantity = max(0, pallet.lot.produced_quantity - (pallet.quantity or 0))
                    self.db.add(pallet.lot)
                
                pallet.tag_status = "OUT_OF_USE"
                pallet.quantity = 0 # 폐기 시 수량 0

            # LOT 상태 및 수량 연동 (AI_README 기준)
            if pallet.lot:
                sync_lot_status_and_quantity(pallet.lot_id, self.db)
                
            
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

            # FIFO 전용 이벤트 발송 (IN 위치 스캔 시 항상 발송)
            if location.location_type == "IN":
                await sio_server.emit('fifo_scan', {
                    'pallet_id': pallet.id,
                    'pallet_no': pallet.pallet_no,
                    'lot_no': pallet.lot.lot_number if pallet.lot else None,
                    'scan_time': scan_time.isoformat(),
                    'is_violation': fifo_warning is not None,
                    'status': 'VIOLATION' if fifo_warning else 'OK'
                })

            # pallet_updated 이벤트 발송 (FIFO 페이지 즉시 갱신용)
            await sio_server.emit('pallet_updated', {
                'pallet_id': pallet.id,
                'pallet_no': pallet.pallet_no,
                'status': next_status,
                'tag_status': pallet.tag_status
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

    def _handle_consuming_genealogy(self, pallet: Pallet, location: RFIDReaderLocation):
        """원자재/재공품 투입 시작 시 현재 공정에서 생산 중인(Producing) 팔레트들과 연결"""
        try:
            if not pallet.lot_id: return
            
            producing_pallets = self.db.query(Pallet).filter(
                Pallet.current_process_id == location.process_id,
                Pallet.status == "Producing",
                Pallet.id != pallet.id
            ).all()

            for pp in producing_pallets:
                if pp.lot_id:
                    # 투입된 팔레트의 수량이 아닌, 생산 중인 팔레트의 수량만큼 소비된 것으로 기록 (1:1 대응 원칙)
                    self._record_genealogy_link(pallet.lot_id, pp.lot_id, location.process_id, pp.quantity, accumulate=True)
            self.db.flush()
        except Exception as e:
            print(f"  [CONSUME_GENEALOGY_ERROR] {e}")

    def _auto_consume_raw_material(self, pallet: Pallet, location: RFIDReaderLocation):
        """첫 공정(샤링)에서 RAW(원자재)를 FIFO 기준으로 자동 소비하고 족보(Genealogy)를 생성"""
        from app.models.item import Item
            
        raw_lot = self.db.query(Lot).join(Item, Lot.item_id == Item.id).filter(
            Item.item_type == "RAW",
            Lot.status.in_(["STOCK", "PROCESS", "WAIT"]),
            Lot.quantity > 0
        ).order_by(Lot.created_at.asc()).with_for_update().first()
        
        if raw_lot:
            consume_qty = pallet.quantity or 0
            if consume_qty <= 0 and pallet.lot and pallet.lot.item:
                consume_qty = pallet.lot.item.pallet_capacity or 0

            # 실제 재고보다 많이 소비되면 재고를 0으로 맞춤 (단순 차감)
            actual_consume = min(raw_lot.quantity, consume_qty)
            
            raw_lot.quantity -= actual_consume
            # 상태는 아래 sync_lot_status_and_quantity에서 수량 기반으로 자동 갱신됨
                
            self._record_genealogy_link(raw_lot.id, pallet.lot_id, location.process_id, actual_consume, accumulate=True)
            self.db.add(raw_lot)
            self.db.flush()
            
            # [Added] RAW LOT 상태 동기화
            from app.services.lot_service import sync_lot_status_and_quantity
            sync_lot_status_and_quantity(raw_lot.id, self.db)
            print(f"  [AUTO_RAW_CONSUME] Consumed {actual_consume} from RAW LOT {raw_lot.lot_number}")
        else:
            print(f"  [AUTO_RAW_CONSUME] Warning: No available RAW LOT found in STOCK for automatic consumption.")

    def _handle_production_genealogy(self, pallet: Pallet, location: RFIDReaderLocation, previous_status: str):
        """생산 시작/완료 시 현재 공정에서 소비 중인(Consuming) 팔레트들과 연결"""
        try:
            if not pallet.lot_id: return

            # [Added] 첫 공정(샤링 등)의 경우: RAW 품목(팔레트 없음)을 자동 소비(FIFO)하여 족보 연결
            process = location.process
            is_first = getattr(process, 'is_first_process', False)
            if not is_first and process and getattr(process, 'process_order', 0) <= 1:
                is_first = True

            if is_first:
                # 새 팔레트가 생산될 때에만 원자재 소비 (중복 차감 방지)
                if previous_status in ["Empty", "Generated"]:
                    self._auto_consume_raw_material(pallet, location)
                return

            # 새 팔레트가 생산될 때만 소비 팔레트와 연결
            if previous_status in ["Empty", "Generated"]:
                consuming_pallets = self.db.query(Pallet).filter(
                    Pallet.current_process_id == location.process_id,
                    Pallet.status == "Consuming",
                    Pallet.id != pallet.id
                ).all()

                for cp in consuming_pallets:
                    if cp.lot_id:
                        # 현재 생산 시작하는 팔레트의 수량만큼 족보에 누적 (cp.quantity는 투입 팔레트 전체 수량이므로 부적절)
                        self._record_genealogy_link(cp.lot_id, pallet.lot_id, location.process_id, pallet.quantity, accumulate=True)
                self.db.flush()
        except Exception as e:
            print(f"  [PROD_GENEALOGY_ERROR] {e}")

    def _record_genealogy_link(self, input_lot_id, output_lot_id, process_id, qty_consumed, qty_produced=None, accumulate=False):
        """중복 확인 후 Genealogy 링크 기록 (누적 가능)"""
        # 별도로 지정하지 않으면 소비 수량과 생산 수량을 동일하게 간주 (1:1 공정)
        if qty_produced is None:
            qty_produced = qty_consumed
            
        existing = self.db.query(LotGenealogy).filter(
            LotGenealogy.input_lot_id == input_lot_id,
            LotGenealogy.output_lot_id == output_lot_id,
            LotGenealogy.process_id == process_id
        ).first()

        if existing:
            if accumulate:
                existing.quantity_consumed = (existing.quantity_consumed or 0) + (qty_consumed or 0)
                existing.quantity_produced = (existing.quantity_produced or 0) + (qty_produced or 0)
                self.db.add(existing)
                print(f"  [GENEALOGY] Updated Lot {input_lot_id} -> Lot {output_lot_id} (Cons: {existing.quantity_consumed}, Prod: {existing.quantity_produced})")
        else:
            genealogy = LotGenealogy(
                input_lot_id=input_lot_id,
                output_lot_id=output_lot_id,
                process_id=process_id,
                quantity_consumed=qty_consumed or 0,
                quantity_produced=qty_produced or 0
            )
            self.db.add(genealogy)
            print(f"  [GENEALOGY] Linked Lot {input_lot_id} -> Lot {output_lot_id} at process {process_id} (Cons: {qty_consumed}, Prod: {qty_produced})")

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
        """FIFO 검증 - 동일 품목의 Stock 팔레트 중 더 일찍 생산된(Stock이 된) 재고가 있는지 확인"""
        if pallet.status != "Stock" or not pallet.lot:
            return None

        # 동일 품목의 Stock 상태 팔레트 중 더 오래된 것 조회 
        older_stock = self.db.query(Pallet).join(Lot).filter(
            Pallet.status == "Stock",
            Pallet.id != pallet.id,
            Lot.item_id == pallet.lot.item_id
        ).filter(
            (Pallet.created_at < pallet.created_at) |
            ((Pallet.created_at == pallet.created_at) & (Pallet.id < pallet.id))
        ).order_by(Pallet.created_at.asc(), Pallet.id.asc()).first()

        if older_stock:
            days_old = (datetime.now() - older_stock.created_at).days
            return FIFOWarning(
                type="FIFO_VIOLATION",
                message=f"FIFO 위반: 동일 품목의 가장 오래된 재고(팔레트: {older_stock.pallet_no})를 먼저 투입해야 합니다.",
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
