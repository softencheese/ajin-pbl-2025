"""대시보드 및 모니터링 스키마"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from app.schemas.common import BaseSchema


class DashboardSummary(BaseSchema):
    """대시보드 요약 정보"""
    active_pallets: int = Field(..., description="활성 팔레트 수")
    total_stock: int = Field(..., description="총 재고 수량")
    today_production: int = Field(..., description="금일 생산량")
    reader_status: Dict[str, int] = Field(..., description="리더기 상태 (connected, total)")


class ProcessStatus(BaseSchema):
    """공정별 상태"""
    process_id: int
    process_name: str
    production_line: Optional[str] = None
    active_pallets: int = Field(default=0, description="활성 팔레트 수")
    status_breakdown: Dict[str, int] = Field(default_factory=dict, description="상태별 팔레트 수")


class ProcessStatusList(BaseSchema):
    """공정별 현황 목록"""
    processes: List[ProcessStatus]
    total_active_pallets: int
    last_updated: datetime


class ReaderStatus(BaseSchema):
    """리더기 상태"""
    id: int
    port_name: str
    process_name: Optional[str] = None
    location_type: str
    status: str = Field(..., description="CONNECTED, DISCONNECTED, ERROR")
    last_scan_time: Optional[datetime] = None
    is_active: bool = True
    error: Optional[str] = None


class ReaderStatusList(BaseSchema):
    """리더기 상태 목록"""
    readers: List[ReaderStatus]


class LotStock(BaseSchema):
    """LOT별 재고 정보"""
    lot_no: str
    pallet_no: Optional[str] = None
    production_date: date
    days_old: int
    quantity: int
    status: str = Field(..., description="urgent, warning, normal")


class StockItem(BaseSchema):
    """품번별 재고 정보"""
    part_number: str
    part_name: Optional[str] = None
    vehicle_model: Optional[str] = None
    process_name: Optional[str] = None
    production_line: Optional[str] = None
    lots: List[LotStock] = []
    
    @property
    def total_quantity(self) -> int:
        return sum(lot.quantity for lot in self.lots)
    
    @property
    def pallet_count(self) -> int:
        return len(self.lots)


class StockInventoryResponse(BaseSchema):
    """재고 현황 응답"""
    stock_items: List[StockItem]
