"""LOT 족보(Genealogy) 라우터"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.lot import Lot
from app.models.lot_genealogy import LotGenealogy
from app.models.item import Item
from app.models.process import Process
from app.schemas.lot_genealogy import (
    LotGenealogyCreate, 
    LotGenealogyResponse, 
    LotGenealogyWithDetails
)

router = APIRouter()


@router.get("/{lot_id}")
def get_lot_genealogy(lot_id: int, db: Session = Depends(get_db)):
    """특정 LOT의 족보 조회 (부모 및 자식 LOT)"""
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="LOT을 찾을 수 없습니다")
    
    item = db.query(Item).filter(Item.id == lot.item_id).first()
    
    # 부모 LOT 조회 (이 LOT를 만들기 위해 사용된 LOT들)
    parents = db.query(LotGenealogy).filter(LotGenealogy.output_lot_id == lot_id).all()
    parent_list = []
    for g in parents:
        parent_lot = db.query(Lot).filter(Lot.id == g.input_lot_id).first()
        parent_item = db.query(Item).filter(Item.id == parent_lot.item_id).first() if parent_lot else None
        if parent_lot and parent_item:
            parent_list.append({
                "lot_number": parent_lot.lot_number,
                "item_code": parent_item.item_code,
                "item_type": parent_item.item_type,
                "quantity_consumed": g.quantity_consumed
            })
    
    # 자식 LOT 조회 (이 LOT가 사용된 LOT들)
    children = db.query(LotGenealogy).filter(LotGenealogy.input_lot_id == lot_id).all()
    children_list = []
    for g in children:
        child_lot = db.query(Lot).filter(Lot.id == g.output_lot_id).first()
        child_item = db.query(Item).filter(Item.id == child_lot.item_id).first() if child_lot else None
        if child_lot and child_item:
            children_list.append({
                "lot_number": child_lot.lot_number,
                "item_code": child_item.item_code,
                "item_type": child_item.item_type,
                "quantity_consumed": g.quantity_consumed
            })
    
    return {
        "lot": {
            "id": lot.id,
            "lot_number": lot.lot_number,
            "item_code": item.item_code if item else None
        },
        "parents": parent_list,
        "children": children_list
    }


@router.post("", response_model=LotGenealogyResponse, status_code=201)
def create_lot_genealogy(data: LotGenealogyCreate, db: Session = Depends(get_db)):
    """LOT 족보 수동 추가"""
    # 입력 LOT 확인
    input_lot = db.query(Lot).filter(Lot.id == data.input_lot_id).first()
    if not input_lot:
        raise HTTPException(status_code=404, detail="투입 LOT를 찾을 수 없습니다")
    
    # 출력 LOT 확인
    output_lot = db.query(Lot).filter(Lot.id == data.output_lot_id).first()
    if not output_lot:
        raise HTTPException(status_code=404, detail="생성 LOT를 찾을 수 없습니다")
    
    # 공정 확인
    process = db.query(Process).filter(Process.id == data.process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="공정을 찾을 수 없습니다")
    
    # 순환 참조 방지 (자기 자신을 부모로 지정)
    if data.input_lot_id == data.output_lot_id:
        raise HTTPException(status_code=400, detail="같은 LOT를 투입과 생성에 지정할 수 없습니다")
    
    genealogy = LotGenealogy(**data.model_dump())
    db.add(genealogy)
    db.commit()
    db.refresh(genealogy)
    return genealogy
