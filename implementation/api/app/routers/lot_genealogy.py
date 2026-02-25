"""LOT 족보(Genealogy) 라우터"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, aliased
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.lot import Lot
from app.models.lot_genealogy import LotGenealogy
from app.models.item import Item
from app.models.process import Process
from app.schemas.lot_genealogy import (
    LotGenealogyCreate, 
    LotGenealogyResponse, 
    LotGenealogyWithDetails
)

from app.core.permissions import PermissionChecker
from app.models.user import User

router = APIRouter()


@router.get("/history", response_model=list[LotGenealogyWithDetails])
def get_genealogy_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("lots", "read"))
):
    """모든 LOT 족보 이력 조회 (권한: lots:read)"""
    # Join queries to get details
    LotIn = aliased(Lot)
    LotOut = aliased(Lot)
    ItemIn = aliased(Item)
    ItemOut = aliased(Item)

    query = db.query(
        LotGenealogy.id,
        LotIn.lot_number.label("input_lot_number"),
        ItemIn.item_code.label("input_item_code"),
        ItemIn.item_type.label("input_item_type"),
        LotOut.lot_number.label("output_lot_number"),
        ItemOut.item_code.label("output_item_code"),
        ItemOut.item_type.label("output_item_type"),
        Process.process_name.label("process_name"),
        LotGenealogy.quantity_consumed.label("quantity_consumed"),
        LotGenealogy.quantity_produced.label("quantity_produced"),
        LotGenealogy.created_at.label("created_at")
    ).outerjoin(LotIn, LotGenealogy.input_lot_id == LotIn.id) \
     .outerjoin(ItemIn, LotIn.item_id == ItemIn.id) \
     .outerjoin(LotOut, LotGenealogy.output_lot_id == LotOut.id) \
     .outerjoin(ItemOut, LotOut.item_id == ItemOut.id) \
     .outerjoin(Process, LotGenealogy.process_id == Process.id) \
     .order_by(LotGenealogy.created_at.desc())

    return query.all()


@router.get("/all", response_model=list[LotGenealogyResponse])
def get_all_lot_genealogy(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("lots", "read"))
):
    """모든 LOT 족보 원본 데이터 조회 (권한: lots:read)"""
    return db.query(LotGenealogy).all()


@router.get("/{lot_id}")
def get_lot_genealogy(
    lot_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("lots", "read"))
):
    """특정 LOT의 족보 조회 (부모 및 자식 LOT) (권한: lots:read)"""
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
                "quantity_consumed": g.quantity_consumed,
                "quantity_produced": g.quantity_produced,
                "process_name": g.process.process_name if g.process else "Unknown"
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
                "quantity_consumed": g.quantity_consumed,
                "quantity_produced": g.quantity_produced,
                "process_name": g.process.process_name if g.process else "Unknown"
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
def create_lot_genealogy(
    data: LotGenealogyCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("lots", "write"))
):
    """LOT 족보 수동 추가 (권한: lots:write)"""
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
