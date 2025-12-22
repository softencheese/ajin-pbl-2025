"""RFID 리더기 위치 스키마"""
from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.common import BaseSchema, TimestampSchema


class ReaderLocationBase(BaseModel):
    port_name: str = Field(..., description="포트 이름 (COM3, 192.168.1.100:9001)")
    process_id: Optional[int] = Field(None, description="공정 ID (미등록 시 None)")
    location_type: Optional[str] = Field(None, description="위치 타입 (IN, OUT, HOLD, DEFECT, FINISH, RETURN)")
    description: Optional[str] = Field(None, description="리더기 설명")
    is_active: bool = Field(default=True, description="활성 여부")


class ReaderLocationCreate(ReaderLocationBase):
    pass


class ReaderLocationUpdate(BaseModel):
    process_id: Optional[int] = None
    location_type: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ReaderLocationResponse(ReaderLocationBase, TimestampSchema):
    id: int
    
    # 공정 정보 포함
    display_name: Optional[str] = None
    
    # 공정 정보 포함
    process_name: Optional[str] = None
    process_code: Optional[str] = None


class ReaderLocationListResponse(BaseModel):
    items: list[ReaderLocationResponse]
    total: int
    page: int
    per_page: int
    pages: int
