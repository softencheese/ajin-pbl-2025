"""LOT 스키마"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime


class LotBase(BaseModel):
    """LOT 기본 필드"""
    item_id: int = Field(..., description="품목 ID")
    quantity: int = Field(..., description="수량")
    production_date: date = Field(..., description="생산일 또는 입고일")
    worker_name: Optional[str] = Field(None, description="작업자명")
    qc_passed: bool = Field(default=False, description="QC 합격 여부")
    barcode: Optional[str] = Field(None, description="실물 바코드 번호 (라벨 스캔용)")
    notes: Optional[str] = Field(None, description="비고")


class LotReceiving(BaseModel):
    """원자재 입고 LOT 생성 요청"""
    item_id: int = Field(..., description="품목 ID (RAW 타입이어야 함)")
    quantity: int = Field(..., description="입고 수량")
    production_date: date = Field(..., description="입고일")
    supplier: Optional[str] = Field(None, description="공급사 (기본 공급사와 다를 경우)")
    barcode: Optional[str] = Field(None, description="실물 바코드 번호 (라벨 스캔용)")
    notes: Optional[str] = Field(None, description="비고")


class LotCreate(LotBase):
    """생산 LOT 생성 요청"""
    process_id: int = Field(..., description="공정 ID")
    supplier: Optional[str] = Field(None, description="공급사")
    input_lots: Optional[List["InputLotInfo"]] = Field(None, description="투입 LOT 정보 목록")
    palette_capacity: Optional[int] = Field(None, description="팔레트당 적재량 (팔레트 자동 생성용)")


class InputLotInfo(BaseModel):
    """투입 LOT 정보"""
    lot_id: int = Field(..., description="투입 LOT ID")
    quantity_consumed: int = Field(..., description="소비 수량")


class LotUpdate(BaseModel):
    """LOT 수정 요청"""
    quantity: Optional[int] = None
    status: Optional[str] = None
    worker_name: Optional[str] = None
    qc_passed: Optional[bool] = None
    notes: Optional[str] = None


class LotStatusUpdate(BaseModel):
    """LOT 상태 변경 요청"""
    status: str = Field(..., description="새 상태 (WAIT, PROCESS, STOCK, CONSUMED, SHIPPED, HOLD, DEFECT)")
    notes: Optional[str] = Field(None, description="변경 사유")


class ItemInfo(BaseModel):
    """품목 정보 (LOT 응답에 포함)"""
    id: int
    item_code: str
    item_name: str
    item_type: str

    model_config = ConfigDict(from_attributes=True)


class LotResponse(BaseModel):
    """LOT 응답"""
    id: int
    lot_number: str
    barcode: Optional[str] = None
    item_id: int
    quantity: int
    initial_quantity: int
    status: str
    production_date: date
    process_id: Optional[int] = None
    supplier: Optional[str] = None
    worker_name: Optional[str] = None
    qc_passed: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 연관 정보
    item: Optional[ItemInfo] = None
    process_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LotListResponse(BaseModel):
    """LOT 목록 응답"""
    items: List[LotResponse]
    total: int
    page: int
    per_page: int
    pages: int


# Forward reference 해결
LotCreate.model_rebuild()
