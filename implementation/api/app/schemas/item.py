from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ItemBase(BaseModel):
    """품목 기본 필드"""
    item_code: str = Field(..., description="품번 또는 원자재코드 (고유)")
    item_name: str = Field(..., description="품명")
    item_type: str = Field(..., description="품목 유형 (RAW, WIP, PRODUCT)")
    unit: str = Field(default="EA", description="단위")
    spec: Optional[str] = Field(None, description="규격 (LH/RH, 색상, 재질 등)")
    vehicle_model: Optional[str] = Field(None, description="적용 차종 (JX1, NE)")
    default_supplier: Optional[str] = Field(None, description="기본 공급사 (원자재인 경우)")


class ItemCreate(ItemBase):
    """품목 생성 요청"""
    pass


class ItemUpdate(BaseModel):
    """품목 수정 요청"""
    item_name: Optional[str] = None
    item_type: Optional[str] = None
    unit: Optional[str] = None
    spec: Optional[str] = None
    vehicle_model: Optional[str] = None
    default_supplier: Optional[str] = None
    is_active: Optional[bool] = None


class ItemResponse(ItemBase):
    """품목 응답"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ItemListResponse(BaseModel):
    """품목 목록 응답"""
    items: list[ItemResponse]
    total: int
    page: int
    per_page: int
    pages: int
