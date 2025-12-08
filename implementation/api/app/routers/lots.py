"""LOT 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.lot import Lot
from app.models.part import Part
from app.models.material import RawMaterial
from app.schemas.lot import (
    LotCreate,
    LotResponse,
    LotListResponse
)

router = APIRouter()


@router.get("", response_model=LotListResponse)
async def list_lots(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    part_id: Optional[int] = None,
    process_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """중간품 LOT 목록 조회"""
    query = db.query(Lot)
    
    if part_id:
        query = query.filter(Lot.part_id == part_id)
    if process_id:
        query = query.filter(Lot.process_id == process_id)
    if date_from:
        query = query.filter(Lot.production_date >= date_from)
    if date_to:
        query = query.filter(Lot.production_date <= date_to)
    
    total = query.count()
    items = query.order_by(Lot.production_date.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    return LotListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.get("/{id}", response_model=LotResponse)
async def get_lot(id: int, db: Session = Depends(get_db)):
    """LOT 상세 조회"""
    lot = db.query(Lot).filter(Lot.id == id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    return lot


@router.post("", response_model=LotResponse, status_code=201)
async def create_lot(data: LotCreate, db: Session = Depends(get_db)):
    """중간품 LOT 생성"""
    # LOT 번호 중복 체크
    existing = db.query(Lot).filter(Lot.lot_no == data.lot_no).first()
    if existing:
        raise HTTPException(status_code=409, detail="Lot number already exists")
    
    # 품번 검증 (중간품만 허용)
    part = db.query(Part).filter(Part.id == data.part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    if part.is_assembly:
        raise HTTPException(
            status_code=422, 
            detail="Assembly parts should use /assembly-lots endpoint"
        )
    
    # 원자재 검증 (필수)
    if not data.material_id:
        raise HTTPException(status_code=422, detail="Material ID is required")
    
    material = db.query(RawMaterial).filter(
        RawMaterial.id == data.material_id
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    lot = Lot(**data.model_dump())
    lot.assembly_level = 0  # 중간품은 항상 0
    
    db.add(lot)
    db.commit()
    db.refresh(lot)
    
    return lot
