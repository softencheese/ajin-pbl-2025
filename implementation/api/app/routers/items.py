"""품목(Items) 라우터"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse, ItemListResponse

router = APIRouter()


@router.get("", response_model=ItemListResponse)
def list_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    item_type: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """품목 목록 조회"""
    query = db.query(Item)
    
    if search:
        query = query.filter(
            (Item.item_code.ilike(f"%{search}%")) |
            (Item.item_name.ilike(f"%{search}%"))
        )
    
    if item_type:
        query = query.filter(Item.item_type == item_type)
    
    if is_active is not None:
        query = query.filter(Item.is_active == is_active)
    
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    pages = (total + per_page - 1) // per_page
    
    return ItemListResponse(
        items=[ItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """품목 상세 조회"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없습니다")
    return item


@router.post("", response_model=ItemResponse, status_code=201)
def create_item(item_data: ItemCreate, db: Session = Depends(get_db)):
    """품목 등록"""
    # 품목코드 중복 검사
    existing = db.query(Item).filter(Item.item_code == item_data.item_code).first()
    if existing:
        raise HTTPException(status_code=409, detail="이미 존재하는 품목코드입니다")
    
    # item_type 검증
    if item_data.item_type not in ["RAW", "WIP", "PRODUCT"]:
        raise HTTPException(status_code=400, detail="item_type은 RAW, WIP, PRODUCT 중 하나여야 합니다")
    
    item = Item(**item_data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item_data: ItemUpdate, db: Session = Depends(get_db)):
    """품목 수정"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없습니다")
    
    update_data = item_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """품목 삭제 (사용 이력 없는 경우만)"""
    from app.models.lot import Lot
    
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없습니다")
    
    # 사용 이력 확인
    lot_count = db.query(Lot).filter(Lot.item_id == item_id).count()
    if lot_count > 0:
        raise HTTPException(status_code=409, detail="사용 이력이 있는 품목은 삭제할 수 없습니다")
    
    db.delete(item)
    db.commit()
    return {"success": True, "message": "품목이 삭제되었습니다"}
