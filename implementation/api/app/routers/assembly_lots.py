"""조립품 LOT 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.assembly import AssemblyLot, AssemblyComponent
from app.models.lot import Lot
from app.models.part import Part
from app.schemas.assembly import (
    AssemblyLotCreate,
    AssemblyLotResponse,
    AssemblyLotListResponse,
    AssemblyComponentCreate,
    AssemblyComponentResponse
)

router = APIRouter()


@router.get("", response_model=AssemblyLotListResponse)
async def list_assembly_lots(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    part_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """조립품 LOT 목록 조회"""
    query = db.query(AssemblyLot)
    
    if part_id:
        query = query.filter(AssemblyLot.part_id == part_id)
    if date_from:
        query = query.filter(AssemblyLot.assembly_date >= date_from)
    if date_to:
        query = query.filter(AssemblyLot.assembly_date <= date_to)
    
    total = query.count()
    items = query.order_by(AssemblyLot.assembly_date.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    return AssemblyLotListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.get("/{id}", response_model=AssemblyLotResponse)
async def get_assembly_lot(id: int, db: Session = Depends(get_db)):
    """조립품 LOT 상세 조회"""
    lot = db.query(AssemblyLot).filter(AssemblyLot.id == id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Assembly lot not found")
    return lot


@router.post("", response_model=AssemblyLotResponse, status_code=201)
async def create_assembly_lot(data: AssemblyLotCreate, db: Session = Depends(get_db)):
    """조립품 LOT 생성"""
    # LOT 번호 중복 체크
    existing = db.query(AssemblyLot).filter(
        AssemblyLot.lot_no == data.lot_no
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Lot number already exists")
    
    # 품번 검증 (조립품만 허용)
    part = db.query(Part).filter(Part.id == data.part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    if not part.is_assembly:
        raise HTTPException(
            status_code=422, 
            detail="Non-assembly parts should use /lots endpoint"
        )
    
    lot = AssemblyLot(**data.model_dump())
    lot.assembly_level = 0  # 초기값, 구성요소 추가 시 계산됨
    
    db.add(lot)
    db.commit()
    db.refresh(lot)
    
    return lot


@router.post("/{id}/components", response_model=AssemblyComponentResponse, status_code=201)
async def add_component(
    id: int, 
    data: AssemblyComponentCreate, 
    db: Session = Depends(get_db)
):
    """조립품 구성 요소 추가"""
    assembly_lot = db.query(AssemblyLot).filter(AssemblyLot.id == id).first()
    if not assembly_lot:
        raise HTTPException(status_code=404, detail="Assembly lot not found")
    
    # 구성 요소 유효성 검증
    component_level = 0
    
    if data.component_lot_id:
        component_lot = db.query(Lot).filter(
            Lot.id == data.component_lot_id
        ).first()
        if not component_lot:
            raise HTTPException(status_code=404, detail="Component lot not found")
        component_level = component_lot.assembly_level
    
    if data.component_assembly_lot_id:
        component_assembly = db.query(AssemblyLot).filter(
            AssemblyLot.id == data.component_assembly_lot_id
        ).first()
        if not component_assembly:
            raise HTTPException(
                status_code=404, 
                detail="Component assembly lot not found"
            )
        component_level = component_assembly.assembly_level
    
    # 둘 중 하나만 있어야 함
    if data.component_lot_id and data.component_assembly_lot_id:
        raise HTTPException(
            status_code=422, 
            detail="Only one of component_lot_id or component_assembly_lot_id should be provided"
        )
    
    if not data.component_lot_id and not data.component_assembly_lot_id:
        raise HTTPException(
            status_code=422, 
            detail="Either component_lot_id or component_assembly_lot_id is required"
        )
    
    component = AssemblyComponent(
        assembly_lot_id=id,
        component_lot_id=data.component_lot_id,
        component_assembly_id=data.component_assembly_lot_id,
        component_pallet_id=data.component_pallet_id,
        required_quantity_per_unit=data.required_quantity_per_unit,
        total_consumed_quantity=data.total_consumed_quantity
    )
    
    db.add(component)
    
    # assembly_level 업데이트 (구성 요소 최대 레벨 + 1)
    new_level = component_level + 1
    if new_level > assembly_lot.assembly_level:
        assembly_lot.assembly_level = new_level
    
    db.commit()
    db.refresh(component)
    
    return component
