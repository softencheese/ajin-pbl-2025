"""RFID 태그 스키마"""
from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.common import BaseSchema, TimestampSchema


class RFIDTagBase(BaseModel):
    epc: str = Field(..., description="RFID EPC 코드")


class RFIDTagCreate(RFIDTagBase):
    pass


class RFIDTagResponse(RFIDTagBase, TimestampSchema):
    id: int
    status: str = Field(default="AVAILABLE", description="태그 상태 (AVAILABLE, IN_USE, DAMAGED)")
    current_pallet_id: Optional[int] = None
    
    # 연결된 팔레트 정보
    pallet_no: Optional[str] = None


class RFIDTagListResponse(BaseSchema):
    items: List[RFIDTagResponse]
    total: int
    page: int
    per_page: int
    pages: int


class RFIDTagStatusUpdate(BaseModel):
    status: str = Field(..., description="새 상태 (AVAILABLE, IN_USE, DAMAGED)")
    reason: Optional[str] = Field(None, description="상태 변경 사유")
