from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class LotGenealogyBase(BaseModel):
    """LOT 족보 기본 필드"""
    input_lot_id: int = Field(..., description="투입 LOT ID (부모)")
    output_lot_id: int = Field(..., description="생성 LOT ID (자식)")
    process_id: int = Field(..., description="발생 공정 ID")
    quantity_consumed: int = Field(..., description="투입 수량")
    quantity_produced: int = Field(..., description="생산 수량")


class LotGenealogyCreate(LotGenealogyBase):
    """LOT 족보 생성 요청"""
    pass


class LotGenealogyResponse(LotGenealogyBase):
    """LOT 족보 응답"""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LotGenealogyWithDetails(BaseModel):
    id: int
    input_lot_number: str
    input_item_code: str
    input_item_type: str
    output_lot_number: str
    output_item_code: str
    output_item_type: str
    process_name: str
    quantity_consumed: int
    quantity_produced: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LotTraceResult(BaseModel):
    """LOT 추적 결과"""
    lot_id: int
    lot_number: str
    item_code: str
    item_type: str
    depth: int


class LotForwardTraceResponse(BaseModel):
    """정방향 추적 응답"""
    root_lot: LotTraceResult
    trace_path: list[LotTraceResult]


class LotBackwardTraceResponse(BaseModel):
    """역방향 추적 응답"""
    leaf_lot: LotTraceResult
    trace_path: list[LotTraceResult]
