"""품번 스키마"""
from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.common import BaseSchema, TimestampSchema


class PartBase(BaseModel):
    part_number: str = Field(..., description="품번")
    part_name: str = Field(..., description="품명")
    part_spec: Optional[str] = Field(None, description="규격")
    vehicle_model: Optional[str] = Field(None, description="적용 차종")
    is_assembly: bool = Field(default=False, description="조립품 여부")
    is_final_product: bool = Field(default=False, description="완제품 여부")


class PartCreate(PartBase):
    pass


class PartUpdate(BaseModel):
    part_name: Optional[str] = None
    part_spec: Optional[str] = None
    vehicle_model: Optional[str] = None
    is_assembly: Optional[bool] = None
    is_final_product: Optional[bool] = None


class PartResponse(PartBase, TimestampSchema):
    id: int


class PartListResponse(BaseSchema):
    items: List[PartResponse]
    total: int
    page: int
    per_page: int
    pages: int
