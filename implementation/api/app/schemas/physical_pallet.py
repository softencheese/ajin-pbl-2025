"""실물 팔레트 스키마"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum





class PhysicalPalletBase(BaseModel):
    """실물 팔레트 기본 스키마"""
    epc: str = Field(..., description="RFID EPC 코드", max_length=100)
    pallet_code: str = Field(..., description="팔레트 실물 코드", max_length=50)
    item_id: Optional[int] = Field(None, description="기본 적재 품목 ID")
    description: Optional[str] = Field(None, description="팔레트 설명", max_length=200)


class PhysicalPalletCreate(PhysicalPalletBase):
    """실물 팔레트 생성 요청"""
    pass


class PhysicalPalletUpdate(BaseModel):
    """실물 팔레트 수정 요청"""
    pallet_code: Optional[str] = Field(None, description="팔레트 실물 코드", max_length=50)
    item_id: Optional[int] = Field(None, description="기본 적재 품목 ID")
    description: Optional[str] = Field(None, description="팔레트 설명", max_length=200)


class PhysicalPalletResponse(BaseModel):
    """실물 팔레트 응답"""
    id: int
    epc: str
    pallet_code: str
    item_id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # 연관 정보
    item_code: Optional[str] = None
    item_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PhysicalPalletListResponse(BaseModel):
    """실물 팔레트 목록 응답"""
    items: List[PhysicalPalletResponse]
    total: int
    page: int
    per_page: int
    pages: int


