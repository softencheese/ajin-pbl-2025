"""추적성 서비스"""
from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.pallet import Pallet, PalletHistory
from app.models.lot import Lot
from app.models.item import Item
from app.models.lot_genealogy import LotGenealogy
from app.schemas.trace import (
    TraceResponse, 
    TraceHistoryItem,
    ForwardTraceResponse,
    ProducedLot,
    PalletSummary,
    ChildLotUsage,
    BackwardTraceResponse,
    ProductInfo,
    ParentLotInfo,
    DrillDownResponse
)


class TraceService:
    def __init__(self, db: Session):
        self.db = db

    def get_pallet_trace(self, pallet_no: str) -> Optional[TraceResponse]:
        """팔레트 이력 조회"""
        pallet = self.db.query(Pallet).filter(Pallet.pallet_no == pallet_no).first()
        if not pallet:
            return None
        
        histories = self.db.query(PalletHistory).filter(
            PalletHistory.pallet_id == pallet.id
        ).order_by(PalletHistory.scan_time.desc()).all()
        
        trace_items = []
        for h in histories:
            trace_items.append(TraceHistoryItem(
                event_time=h.scan_time,
                event_type=h.event_type,
                process_name=h.process.process_name if h.process else None,
                location_type=h.location_type,
                previous_status=h.previous_status,
                current_status=h.new_status,
                worker_name=h.worker_name
            ))
            
        lot_no = None
        item_code = None
        
        if pallet.lot:
            lot_no = pallet.lot.lot_number
            if pallet.lot.item:
                item_code = pallet.lot.item.item_code

        return TraceResponse(
            pallet_no=pallet.pallet_no,
            lot_no=lot_no,
            item_code=item_code,
            histories=trace_items
        )

    def forward_trace(
        self, 
        lot_no: str
    ) -> Optional[ForwardTraceResponse]:
        """정방향 추적 (투입 LOT → 산출 LOT)"""
        root_lot = self.db.query(Lot).filter(Lot.lot_number == lot_no).first()
        
        if not root_lot:
            return None
        
        # 1. 직계 자식 LOT 조회 (1단계만 조회하거나, 재귀적으로 조회해야 함. 여기선 1단계만 예시)
        # TODO: 필요 시 재귀적 탐색 구현
        genealogies = self.db.query(LotGenealogy).filter(
            LotGenealogy.input_lot_id == root_lot.id
        ).all()
        
        produced_lots_map = {} # lot_id -> ProducedLot

        for gen in genealogies:
            output_lot = gen.output_lot
            if output_lot.id not in produced_lots_map:
                # Recursively trace children
                self._trace_children(output_lot, produced_lots_map)
                
        return ForwardTraceResponse(
            root_lot_no=root_lot.lot_number,
            item_code=root_lot.item.item_code,
            item_name=root_lot.item.item_name,
            item_type=root_lot.item.item_type,
            supplier=None, # Lot 모델에 supplier가 있다면 추가
            production_date=root_lot.production_date,
            qc_passed=root_lot.qc_passed,
            produced_lots=list(produced_lots_map.values())
        )

    def _trace_children(self, parent_lot: Lot, produced_lots_map: dict):
        """재귀적으로 하위 LOT 추적"""
        if parent_lot.id in produced_lots_map:
             return

        # 1. 팔레트 조회
        pallets = self.db.query(Pallet).filter(Pallet.lot_id == parent_lot.id).all()
        pallet_summaries = [
            PalletSummary(
                pallet_no=p.pallet_no,
                status=p.status,
                current_process=p.current_process.process_name if p.current_process else None
            ) for p in pallets
        ]

        # 2. 바로 아래 자식들 조회
        child_genes = self.db.query(LotGenealogy).filter(LotGenealogy.input_lot_id == parent_lot.id).all()
        child_usages = []
        
        for cg in child_genes:
            child_lot = cg.output_lot
            child_usages.append(ChildLotUsage(
                child_lot_no=child_lot.lot_number,
                child_item_code=child_lot.item.item_code,
                child_item_name=child_lot.item.item_name,
                quantity_consumed=cg.quantity_consumed
            ))
            
            # 재귀 호출
            self._trace_children(child_lot, produced_lots_map)

        produced_lots_map[parent_lot.id] = ProducedLot(
            lot_no=parent_lot.lot_number,
            item_code=parent_lot.item.item_code,
            item_name=parent_lot.item.item_name,
            quantity=parent_lot.quantity,
            production_date=parent_lot.production_date,
            qc_passed=parent_lot.qc_passed,
            pallets=pallet_summaries,
            child_lots=child_usages
        )
        


    def backward_trace(
        self, 
        lot_no: str
    ) -> Optional[BackwardTraceResponse]:
        """역방향 추적 (산출 LOT → 투입 LOT) - 재귀적으로 원자재까지 추적"""
        
        target_lot = self.db.query(Lot).filter(Lot.lot_number == lot_no).first()
        
        if not target_lot:
            return None
        
        product_info = ProductInfo(
            lot_no=target_lot.lot_number,
            item_code=target_lot.item.item_code,
            item_name=target_lot.item.item_name,
            item_type=target_lot.item.item_type
        )
        
        # 재귀적으로 모든 부모 LOT 조회
        all_parents = []
        visited = set()
        self._trace_parents_recursive(target_lot.id, all_parents, visited)
            
        return BackwardTraceResponse(
            product=product_info,
            parent_lots=all_parents
        )

    def _trace_parents_recursive(self, lot_id: int, result: list, visited: set):
        """재귀적으로 부모 LOT 추적"""
        if lot_id in visited:
            return
        visited.add(lot_id)
        
        genealogies = self.db.query(LotGenealogy).filter(
            LotGenealogy.output_lot_id == lot_id
        ).all()
        
        for gen in genealogies:
            input_lot = gen.input_lot
            result.append(ParentLotInfo(
                lot_no=input_lot.lot_number,
                item_code=input_lot.item.item_code,
                item_name=input_lot.item.item_name,
                quantity_consumed=gen.quantity_consumed,
                supplier=getattr(input_lot, 'supplier', None)
            ))
            # 부모의 부모를 재귀적으로 탐색
            self._trace_parents_recursive(input_lot.id, result, visited)


    def drill_down_search(self, search: str) -> Optional[DrillDownResponse]:
        """드릴다운 검색"""
        search = search.strip()
        # SQL LIKE 와일드카드 이스케이프 (보안)
        safe_search = search.replace("%", r"\%").replace("_", r"\_")
        
        # 1. 팔레트 검색
        pallet = self.db.query(Pallet).filter(
            Pallet.pallet_no.ilike(f"%{safe_search}%", escape="\\") | 
            Pallet.rfid_epc.ilike(f"%{safe_search}%", escape="\\")
        ).first()
        
        if pallet:
            lot_no = pallet.lot.lot_number if pallet.lot else None
            
            return DrillDownResponse(
                search_type="PALLET",
                search_value=pallet.pallet_no,
                backward_trace=self.backward_trace(lot_no) if lot_no else None,
                related_pallets=[PalletSummary(
                    pallet_no=pallet.pallet_no,
                    status=pallet.status,
                    current_process=pallet.current_process.process_name if pallet.current_process else None
                )]
            )
        
        # 2. LOT 검색
        lot = self.db.query(Lot).filter(Lot.lot_number.ilike(f"%{safe_search}%", escape="\\")).first()
        if lot:
            return DrillDownResponse(
                search_type="LOT",
                search_value=lot.lot_number,
                forward_trace=self.forward_trace(lot.lot_number),
                backward_trace=self.backward_trace(lot.lot_number),
                related_pallets=[
                    PalletSummary(
                        pallet_no=p.pallet_no,
                        status=p.status,
                        current_process=p.current_process.process_name if p.current_process else None
                    ) for p in self.db.query(Pallet).filter(Pallet.lot_id == lot.id).all()
                ]
            )
        
        # 3. Item 검색
        item = self.db.query(Item).filter(
            Item.item_code.ilike(f"%{safe_search}%", escape="\\") | 
            Item.item_name.ilike(f"%{safe_search}%", escape="\\")
        ).first()
        
        if item:
             # 해당 아이템으로 생성된 LOT들 중 가장 최근 것 하나 찾아서 예시로 보여주거나, 별도 처리
             # 여기서는 단순히 검색된 아이템 정보만 리턴하거나, 해당 아이템의 최신 LOT를 기반으로 Trace
             
             recent_lot = self.db.query(Lot).filter(Lot.item_id == item.id).order_by(Lot.created_at.desc()).first()
             
             return DrillDownResponse(
                search_type="ITEM",
                search_value=item.item_code,
                forward_trace=self.forward_trace(recent_lot.lot_number) if recent_lot else None,
                related_pallets=[]
            )
        
        return None
