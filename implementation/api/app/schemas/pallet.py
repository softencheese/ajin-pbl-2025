"""팔레트 스키마"""
from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.common import BaseSchema, TimestampSchema


class PalletBase(BaseModel):
    pallet_no: str = Field(..., description="팔레트 번호")
    rfid_epc: Optional[str] = Field(None, description="RFID EPC 코드")


class PalletCreate(PalletBase):
    pass


class PalletResponse(PalletBase, TimestampSchema):
    id: int
    status: str = Field(default="Generated", description="팔레트 상태")
    quantity: int = Field(default=0, description="현재 적재 수량")
    
    # 연관 정보
    lot_no: Optional[str] = None
    part_number: Optional[str] = None
    part_name: Optional[str] = None
    current_process_name: Optional[str] = None


class PalletListResponse(BaseSchema):
    items: List[PalletResponse]
    total: int
    page: int
    per_page: int
    pages: int


class PalletLinkLot(BaseModel):
    """LOT 연결 요청"""
    lot_id: Optional[int] = Field(None, description="중간품 LOT ID")
    assembly_lot_id: Optional[int] = Field(None, description="조립품 LOT ID")


class PalletStatusUpdate(BaseModel):
    """상태 강제 변경 (관리자)"""
    status: str = Field(..., description="새 상태")
    reason: Optional[str] = Field(None, description="변경 사유")
