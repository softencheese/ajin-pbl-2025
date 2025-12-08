"""조립품 LOT 스키마"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from app.schemas.common import BaseSchema, TimestampSchema


class AssemblyLotBase(BaseModel):
    lot_no: str = Field(..., description="조립품 LOT 번호")
    part_id: int = Field(..., description="품번 ID (조립품)")
    assembly_date: date = Field(..., description="조립일자")
    quantity: int = Field(..., description="수량")
    worker_name: Optional[str] = Field(None, description="작업자명")
    qc_passed: bool = Field(default=False, description="QC 합격 여부")


class AssemblyLotCreate(AssemblyLotBase):
    pass


class AssemblyLotResponse(AssemblyLotBase, TimestampSchema):
    id: int
    assembly_level: int = Field(default=0, description="조립 레벨")
    
    # 연관 정보
    part_number: Optional[str] = None
    part_name: Optional[str] = None
    is_final_product: Optional[bool] = None


class AssemblyLotListResponse(BaseSchema):
    items: List[AssemblyLotResponse]
    total: int
    page: int
    per_page: int
    pages: int


class AssemblyComponentBase(BaseModel):
    component_lot_id: Optional[int] = Field(None, description="중간품 LOT ID")
    component_assembly_lot_id: Optional[int] = Field(None, description="하위 조립품 LOT ID")
    component_pallet_id: Optional[int] = Field(None, description="투입 팔레트 ID")
    required_quantity_per_unit: int = Field(default=1, description="단위당 필요 수량")
    total_consumed_quantity: int = Field(..., description="총 소비 수량")


class AssemblyComponentCreate(AssemblyComponentBase):
    pass


class AssemblyComponentResponse(AssemblyComponentBase, TimestampSchema):
    id: int
    assembly_lot_id: int
    
    # 연관 정보
    component_lot_no: Optional[str] = None
    component_part_number: Optional[str] = None
