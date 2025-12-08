"""원자재 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.material import RawMaterial
from app.schemas.material import (
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    MaterialListResponse
)

router = APIRouter()


@router.get("", response_model=MaterialListResponse)
async def list_materials(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """원자재 목록 조회"""
    query = db.query(RawMaterial)
    
    if search:
        query = query.filter(
            RawMaterial.coil_number.contains(search) |
            RawMaterial.material_name.contains(search)
        )
    
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return MaterialListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.get("/{id}", response_model=MaterialResponse)
async def get_material(id: int, db: Session = Depends(get_db)):
    """원자재 상세 조회"""
    material = db.query(RawMaterial).filter(RawMaterial.id == id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.post("", response_model=MaterialResponse, status_code=201)
async def create_material(data: MaterialCreate, db: Session = Depends(get_db)):
    """원자재 등록"""
    # 코일 번호 중복 체크
    existing = db.query(RawMaterial).filter(
        RawMaterial.coil_number == data.coil_number
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Coil number already exists")
    
    material = RawMaterial(**data.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.put("/{id}", response_model=MaterialResponse)
async def update_material(id: int, data: MaterialUpdate, db: Session = Depends(get_db)):
    """원자재 수정"""
    material = db.query(RawMaterial).filter(RawMaterial.id == id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(material, key, value)
    
    db.commit()
    db.refresh(material)
    return material


@router.delete("/{id}")
async def delete_material(id: int, db: Session = Depends(get_db)):
    """원자재 삭제 (사용 이력 없는 경우만)"""
    material = db.query(RawMaterial).filter(RawMaterial.id == id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # TODO: 사용 이력 체크 (lots 테이블에서 참조 중인지 확인)
    
    db.delete(material)
    db.commit()
    return {"success": True, "message": "Material deleted"}
