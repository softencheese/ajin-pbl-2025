"""품번 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.part import Part
from app.schemas.part import (
    PartCreate,
    PartUpdate,
    PartResponse,
    PartListResponse
)

router = APIRouter()


@router.get("", response_model=PartListResponse)
async def list_parts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_assembly: Optional[bool] = None,
    is_final_product: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """품번 목록 조회"""
    query = db.query(Part)
    
    if search:
        query = query.filter(
            Part.part_number.contains(search) |
            Part.part_name.contains(search)
        )
    
    if is_assembly is not None:
        query = query.filter(Part.is_assembly == is_assembly)
    
    if is_final_product is not None:
        query = query.filter(Part.is_final_product == is_final_product)
    
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return PartListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.get("/{id}", response_model=PartResponse)
async def get_part(id: int, db: Session = Depends(get_db)):
    """품번 상세 조회"""
    part = db.query(Part).filter(Part.id == id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return part


@router.post("", response_model=PartResponse, status_code=201)
async def create_part(data: PartCreate, db: Session = Depends(get_db)):
    """품번 등록"""
    existing = db.query(Part).filter(Part.part_number == data.part_number).first()
    if existing:
        raise HTTPException(status_code=409, detail="Part number already exists")
    
    part = Part(**data.model_dump())
    db.add(part)
    db.commit()
    db.refresh(part)
    return part


@router.put("/{id}", response_model=PartResponse)
async def update_part(id: int, data: PartUpdate, db: Session = Depends(get_db)):
    """품번 수정"""
    part = db.query(Part).filter(Part.id == id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(part, key, value)
    
    db.commit()
    db.refresh(part)
    return part
