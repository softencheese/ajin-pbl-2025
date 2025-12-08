"""원자재 스키마"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from app.schemas.common import BaseSchema, TimestampSchema


class MaterialBase(BaseModel):
    coil_number: str = Field(..., description="코일 번호")
    material_name: str = Field(..., description="재질명")
    supplier: Optional[str] = Field(None, description="공급업체")
    receipt_date: Optional[date] = Field(None, description="입고일자")
    qc_passed: bool = Field(default=False, description="QC 합격 여부")


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    material_name: Optional[str] = None
    supplier: Optional[str] = None
    receipt_date: Optional[date] = None
    qc_passed: Optional[bool] = None


class MaterialResponse(MaterialBase, TimestampSchema):
    id: int


class MaterialListResponse(BaseSchema):
    items: List[MaterialResponse]
    total: int
    page: int
    per_page: int
    pages: int
