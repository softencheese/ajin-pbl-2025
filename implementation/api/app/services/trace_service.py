"""추적성 서비스"""
from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.pallet import Pallet, PalletHistory
from app.models.lot import Lot
from app.models.assembly import AssemblyLot, AssemblyComponent
from app.models.material import RawMaterial
from app.schemas.trace import (
    TraceResponse, 
    TraceHistoryItem,
    ForwardTraceResponse,
    ProducedLot,
    PalletSummary,
    AssemblyUsage,
    BackwardTraceResponse,
    ProductInfo,
    ComponentInfo,
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
        ).order_by(PalletHistory.event_time.desc()).all()
        
        trace_items = []
        for h in histories:
            trace_items.append(TraceHistoryItem(
                event_time=h.event_time,
                event_type=h.event_type,
                process_name=h.process.process_name if h.process else None,
                location_type=h.location_type,
                previous_status=h.previous_status,
                current_status=h.current_status,
                worker_name=h.worker_name
            ))
            
        lot_no = None
        part_number = None
        if pallet.lot:
            lot_no = pallet.lot.lot_no
            part_number = pallet.lot.part.part_number
        elif pallet.assembly_lot:
            lot_no = pallet.assembly_lot.lot_no
            part_number = pallet.assembly_lot.part.part_number

        return TraceResponse(
            pallet_no=pallet.pallet_no,
            lot_no=lot_no,
            part_number=part_number,
            histories=trace_items
        )

    def forward_trace(
        self, 
        coil_number: str, 
        include_assemblies: bool = True
    ) -> Optional[ForwardTraceResponse]:
        """정방향 추적 (원자재 → 제품)"""
        material = self.db.query(RawMaterial).filter(
            RawMaterial.coil_number == coil_number
        ).first()
        
        if not material:
            return None
        
        # 해당 원자재로 생산된 LOT 조회
        lots = self.db.query(Lot).filter(Lot.material_id == material.id).all()
        
        produced_lots = []
        for lot in lots:
            # 팔레트 조회
            pallets = self.db.query(Pallet).filter(Pallet.lot_id == lot.id).all()
            pallet_summaries = [
                PalletSummary(
                    pallet_no=p.pallet_no,
                    status=p.status,
                    current_process=p.current_process.process_name if p.current_process else None
                ) for p in pallets
            ]
            
            # 조립품 사용 정보 조회
            assembly_usages = []
            if include_assemblies:
                components = self.db.query(AssemblyComponent).filter(
                    AssemblyComponent.component_lot_id == lot.id
                ).all()
                
                for comp in components:
                    if comp.assembly_lot:
                        assembly_usages.append(AssemblyUsage(
                            assembly_lot_no=comp.assembly_lot.lot_no,
                            assembly_part_number=comp.assembly_lot.part.part_number,
                            assembly_part_name=comp.assembly_lot.part.part_name,
                            assembly_level=comp.assembly_lot.assembly_level,
                            is_final_product=comp.assembly_lot.part.is_final_product,
                            quantity_used=comp.total_consumed_quantity
                        ))
            
            produced_lots.append(ProducedLot(
                lot_no=lot.lot_no,
                part_number=lot.part.part_number,
                part_name=lot.part.part_name,
                quantity=lot.quantity,
                production_date=lot.production_date,
                qc_passed=lot.qc_passed,
                pallets=pallet_summaries,
                used_in_assemblies=assembly_usages
            ))
        
        return ForwardTraceResponse(
            coil_number=material.coil_number,
            material_name=material.material_name,
            supplier=material.supplier,
            receipt_date=material.receipt_date,
            qc_passed=material.qc_passed,
            produced_lots=produced_lots
        )

    def backward_trace(
        self, 
        lot_no: Optional[str] = None, 
        assembly_lot_no: Optional[str] = None
    ) -> Optional[BackwardTraceResponse]:
        """역방향 추적 (제품 → 원자재)"""
        
        if assembly_lot_no:
            # 조립품 LOT 조회
            assembly_lot = self.db.query(AssemblyLot).filter(
                AssemblyLot.lot_no == assembly_lot_no
            ).first()
            
            if not assembly_lot:
                return None
            
            product = ProductInfo(
                lot_no=assembly_lot.lot_no,
                part_number=assembly_lot.part.part_number,
                part_name=assembly_lot.part.part_name,
                is_assembly=True,
                assembly_level=assembly_lot.assembly_level
            )
            
            # 구성 요소 조회
            components = []
            raw_materials = []
            
            for comp in assembly_lot.components:
                if comp.component_lot:
                    components.append(ComponentInfo(
                        lot_no=comp.component_lot.lot_no,
                        part_number=comp.component_lot.part.part_number,
                        part_name=comp.component_lot.part.part_name,
                        coil_number=comp.component_lot.material.coil_number if comp.component_lot.material else None,
                        quantity_used=comp.total_consumed_quantity
                    ))
                    
                    # 원자재 정보 수집
                    if comp.component_lot.material:
                        mat = comp.component_lot.material
                        raw_materials.append({
                            "coil_number": mat.coil_number,
                            "material_name": mat.material_name,
                            "supplier": mat.supplier
                        })
            
            return BackwardTraceResponse(
                product=product,
                components=components,
                raw_materials=raw_materials
            )
        
        elif lot_no:
            # 중간품 LOT 조회
            lot = self.db.query(Lot).filter(Lot.lot_no == lot_no).first()
            
            if not lot:
                return None
            
            product = ProductInfo(
                lot_no=lot.lot_no,
                part_number=lot.part.part_number,
                part_name=lot.part.part_name,
                is_assembly=False,
                assembly_level=0
            )
            
            raw_materials = []
            if lot.material:
                raw_materials.append({
                    "coil_number": lot.material.coil_number,
                    "material_name": lot.material.material_name,
                    "supplier": lot.material.supplier
                })
            
            return BackwardTraceResponse(
                product=product,
                components=[],
                raw_materials=raw_materials
            )
        
        return None

    def drill_down_search(self, search: str) -> Optional[DrillDownResponse]:
        """드릴다운 검색"""
        search = search.strip()
        
        # 팔레트 검색
        pallet = self.db.query(Pallet).filter(
            Pallet.pallet_no.contains(search) | 
            Pallet.rfid_epc.contains(search)
        ).first()
        
        if pallet:
            lot_no = pallet.lot.lot_no if pallet.lot else None
            assembly_lot_no = pallet.assembly_lot.lot_no if pallet.assembly_lot else None
            
            return DrillDownResponse(
                search_type="PALLET",
                search_value=pallet.pallet_no,
                backward_trace=self.backward_trace(lot_no, assembly_lot_no) if (lot_no or assembly_lot_no) else None,
                related_pallets=[PalletSummary(
                    pallet_no=pallet.pallet_no,
                    status=pallet.status,
                    current_process=pallet.current_process.process_name if pallet.current_process else None
                )]
            )
        
        # LOT 검색
        lot = self.db.query(Lot).filter(Lot.lot_no.contains(search)).first()
        if lot:
            return DrillDownResponse(
                search_type="LOT",
                search_value=lot.lot_no,
                forward_trace=self.forward_trace(lot.material.coil_number) if lot.material else None,
                backward_trace=self.backward_trace(lot_no=lot.lot_no),
                related_pallets=[
                    PalletSummary(
                        pallet_no=p.pallet_no,
                        status=p.status,
                        current_process=p.current_process.process_name if p.current_process else None
                    ) for p in self.db.query(Pallet).filter(Pallet.lot_id == lot.id).all()
                ]
            )
        
        # 코일 검색
        material = self.db.query(RawMaterial).filter(
            RawMaterial.coil_number.contains(search)
        ).first()
        if material:
            return DrillDownResponse(
                search_type="COIL",
                search_value=material.coil_number,
                forward_trace=self.forward_trace(material.coil_number),
                related_pallets=[]
            )
        
        return None
