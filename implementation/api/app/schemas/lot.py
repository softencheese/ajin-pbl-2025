"""LOT 스키마"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from app.schemas.common import BaseSchema, TimestampSchema


class LotBase(BaseModel):
    lot_no: str = Field(..., description="LOT 번호")
    part_id: int = Field(..., description="품번 ID")
    process_id: int = Field(..., description="공정 ID")
    material_id: int = Field(..., description="원자재 ID (필수)")
    quantity: int = Field(..., description="수량")
    production_date: date = Field(..., description="생산일자")
    worker_name: Optional[str] = Field(None, description="작업자명")
    qc_passed: bool = Field(default=False, description="QC 합격 여부")


class LotCreate(LotBase):
    pass


class LotResponse(LotBase, TimestampSchema):
    id: int
    assembly_level: int = Field(default=0, description="조립 레벨 (중간품은 항상 0)")
    
    # 연관 정보
    part_number: Optional[str] = None
    part_name: Optional[str] = None
    process_name: Optional[str] = None
    coil_number: Optional[str] = None


class LotListResponse(BaseSchema):
    items: List[LotResponse]
    total: int
    page: int
    per_page: int
    pages: int
