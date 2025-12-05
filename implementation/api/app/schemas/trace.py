"""추적성 스키마"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime, date
from app.schemas.common import BaseSchema


class TraceHistoryItem(BaseSchema):
    """팔레트 이력 항목"""
    event_time: datetime
    event_type: str
    process_name: Optional[str] = None
    location_type: Optional[str] = None
    previous_status: Optional[str] = None
    current_status: str
    worker_name: Optional[str] = None


class TraceResponse(BaseSchema):
    """팔레트 이력 응답"""
    pallet_no: str
    lot_no: Optional[str] = None
    part_number: Optional[str] = None
    histories: List[TraceHistoryItem] = []


# 정방향 추적 (원자재 → 제품)
class PalletSummary(BaseSchema):
    """팔레트 요약 정보"""
    pallet_no: str
    status: str
    current_process: Optional[str] = None


class AssemblyUsage(BaseSchema):
    """조립품 사용 정보"""
    assembly_lot_no: str
    assembly_part_number: str
    assembly_part_name: Optional[str] = None
    assembly_level: int
    is_final_product: bool
    quantity_used: int


class ProducedLot(BaseSchema):
    """생산된 LOT 정보"""
    lot_no: str
    part_number: str
    part_name: Optional[str] = None
    quantity: int
    production_date: date
    qc_passed: bool
    pallets: List[PalletSummary] = []
    used_in_assemblies: List[AssemblyUsage] = []


class ForwardTraceResponse(BaseSchema):
    """정방향 추적 응답"""
    coil_number: str
    material_name: str
    supplier: Optional[str] = None
    receipt_date: Optional[date] = None
    qc_passed: bool
    produced_lots: List[ProducedLot] = []


# 역방향 추적 (제품 → 원자재)
class ComponentInfo(BaseSchema):
    """구성 요소 정보"""
    lot_no: str
    part_number: str
    part_name: Optional[str] = None
    coil_number: Optional[str] = None
    quantity_used: Optional[int] = None


class ProductInfo(BaseSchema):
    """제품 정보"""
    lot_no: str
    part_number: str
    part_name: Optional[str] = None
    is_assembly: bool = False
    assembly_level: int = 0


class BackwardTraceResponse(BaseSchema):
    """역방향 추적 응답"""
    product: ProductInfo
    components: List[ComponentInfo] = []
    raw_materials: List[dict] = []  # 원자재 정보


# 드릴다운 검색
class DrillDownResponse(BaseSchema):
    """드릴다운 검색 응답"""
    search_type: str = Field(..., description="검색 타입 (PALLET, LOT, PART, COIL)")
    search_value: str
    forward_trace: Optional[ForwardTraceResponse] = None
    backward_trace: Optional[BackwardTraceResponse] = None
    related_pallets: List[PalletSummary] = []
