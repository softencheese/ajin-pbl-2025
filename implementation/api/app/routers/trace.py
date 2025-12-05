"""추적성 조회 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.trace_service import TraceService
from app.schemas.trace import (
    TraceResponse, 
    ForwardTraceResponse, 
    BackwardTraceResponse,
    DrillDownResponse
)

router = APIRouter()


@router.get("/pallet/{pallet_no}", response_model=TraceResponse)
async def get_pallet_trace(pallet_no: str, db: Session = Depends(get_db)):
    """
    팔레트 이력 조회
    
    팔레트의 전체 상태 변경 이력을 조회합니다.
    """
    service = TraceService(db)
    trace = service.get_pallet_trace(pallet_no)
    if not trace:
        raise HTTPException(status_code=404, detail="Pallet not found")
    return trace


@router.get("/forward", response_model=ForwardTraceResponse)
async def forward_trace(
    coil_number: str = Query(..., description="코일 번호"),
    include_assemblies: bool = Query(True, description="조립품까지 포함"),
    db: Session = Depends(get_db)
):
    """
    정방향 추적 (원자재 → 제품)
    
    특정 코일에서 생산된 모든 중간품과 조립품을 추적합니다.
    """
    service = TraceService(db)
    result = service.forward_trace(coil_number, include_assemblies)
    if not result:
        raise HTTPException(status_code=404, detail="Coil not found")
    return result


@router.get("/backward", response_model=BackwardTraceResponse)
async def backward_trace(
    lot_no: Optional[str] = Query(None, description="LOT 번호"),
    assembly_lot_no: Optional[str] = Query(None, description="조립품 LOT 번호"),
    db: Session = Depends(get_db)
):
    """
    역방향 추적 (제품 → 원자재)
    
    특정 제품을 구성하는 모든 원자재와 구성품을 추적합니다.
    """
    if not lot_no and not assembly_lot_no:
        raise HTTPException(
            status_code=400, 
            detail="Either lot_no or assembly_lot_no is required"
        )
    
    service = TraceService(db)
    result = service.backward_trace(lot_no, assembly_lot_no)
    if not result:
        raise HTTPException(status_code=404, detail="Lot not found")
    return result


@router.get("/drill-down", response_model=DrillDownResponse)
async def drill_down_search(
    search: str = Query(..., description="검색어 (품번, LOT, 코일, 팔레트 번호)"),
    db: Session = Depends(get_db)
):
    """
    드릴다운 검색
    
    품번, LOT, 코일, 팔레트 번호 등으로 통합 검색하여
    정방향/역방향 추적 결과를 함께 반환합니다.
    """
    service = TraceService(db)
    result = service.drill_down_search(search)
    if not result:
        raise HTTPException(status_code=404, detail="No results found")
    return result
