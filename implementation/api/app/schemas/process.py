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


class ProcessResponse(ProcessBase, TimestampSchema):
    id: int
