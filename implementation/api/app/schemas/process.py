"""공정 스키마"""
from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.common import BaseSchema, TimestampSchema


class ProcessBase(BaseModel):
    process_code: str = Field(..., description="공정 코드")
    process_name: str = Field(..., description="공정명")
    process_order: int = Field(..., description="공정 순서")
    production_line: Optional[str] = Field(None, description="생산 라인")


class ProcessCreate(ProcessBase):
    pass


class ProcessOrderUpdate(BaseModel):
    new_order: int = Field(..., description="새 공정 순서")


class ProcessUpdate(BaseModel):
    process_code: Optional[str] = Field(None, description="공정 코드")
    process_name: Optional[str] = Field(None, description="공정명")
    production_line: Optional[str] = Field(None, description="생산 라인")
    allowed_item_types: Optional[str] = Field(None, description="허용 아이템 타입 (RAW,WIP,PRODUCT)")
    is_first_process: Optional[bool] = Field(None, description="첫 공정 여부")


class ProcessResponse(ProcessBase, TimestampSchema):
    id: int
    allowed_item_types: Optional[str] = None
    is_first_process: Optional[bool] = None
