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
    item_code: Optional[str] = None
    histories: List[TraceHistoryItem] = []


# 정방향 추적 (원자재 → 제품)
class PalletSummary(BaseSchema):
    """팔레트 요약 정보"""
    pallet_no: str
    status: str
    current_process: Optional[str] = None


class ChildLotUsage(BaseSchema):
    """자식 LOT (생성된 LOT) 정보"""
    child_lot_no: str
    child_item_code: str
    child_item_name: Optional[str] = None
    quantity_consumed: int


class ProducedLot(BaseSchema):
    """생산된 LOT 정보"""
    lot_no: str
    item_code: str
    item_name: Optional[str] = None
    quantity: int
    production_date: date
    qc_passed: bool
    pallets: List[PalletSummary] = []
    child_lots: List[ChildLotUsage] = []


class ForwardTraceResponse(BaseSchema):
    """정방향 추적 응답"""
    root_lot_no: str
    item_code: str
    item_name: str
    item_type: str
    supplier: Optional[str] = None # 원자재인 경우
    production_date: Optional[date] = None
    qc_passed: bool
    produced_lots: List[ProducedLot] = []


# 역방향 추적 (제품 → 원자재)
class ParentLotInfo(BaseSchema):
    """부모 LOT (투입된 LOT) 정보"""
    lot_no: str
    item_code: str
    item_name: Optional[str] = None
    quantity_consumed: int
    supplier: Optional[str] = None # 원자재인 경우


class ProductInfo(BaseSchema):
    """제품 정보"""
    lot_no: str
    item_code: str
    item_name: Optional[str] = None
    item_type: str


class BackwardTraceResponse(BaseSchema):
    """역방향 추적 응답"""
    product: ProductInfo
    parent_lots: List[ParentLotInfo] = []


# 드릴다운 검색
class DrillDownResponse(BaseSchema):
    """드릴다운 검색 응답"""
    search_type: str = Field(..., description="검색 타입 (PALLET, LOT, ITEM)")
    search_value: str
    forward_trace: Optional[ForwardTraceResponse] = None
    backward_trace: Optional[BackwardTraceResponse] = None
    related_pallets: List[PalletSummary] = []
