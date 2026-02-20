from sqlalchemy.orm import Session
from app.models.pallet import Pallet
from app.models.lot import Lot
from app.models.item import Item

def sync_lot_status_and_quantity(lot_id: int, db: Session):
    """LOT의 하위 팔레트 상태에 따라 LOT의 상태와 수량을 동기화 (강화된 수량 기준 규칙)"""
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        return
        
    item = db.query(Item).filter(Item.id == lot.item_id).first()
    all_pallets = db.query(Pallet).filter(Pallet.lot_id == lot.id).all()

    # 1. 수량 동기화 (WIP, PRODUCT만 대상. RAW는 직접 수량 차감됨)
    if item and item.item_type != "RAW":
        # Stock, Finished, Deregistered 상태 팔레트의 수량 합
        countable_statuses = ["Stock", "Finished", "Deregistered"]
        lot.quantity = sum(p.quantity or 0 for p in all_pallets if p.status in countable_statuses)

    # 2. 상태 결정
    pallet_statuses = [p.status for p in all_pallets]
    
    # [Rule] 현재 재고가 목표 수량일 때만 STOCK
    if lot.quantity == lot.initial_quantity:
        lot.status = "STOCK"
    # [Rule] 누적수량이 목표수량 이상이고 현재 수량이 0일 때 CONSUMED/SHIPPED
    elif lot.produced_quantity >= lot.initial_quantity and lot.quantity == 0:
        if item and item.item_type == "PRODUCT":
            lot.status = "SHIPPED"
        else:
            lot.status = "CONSUMED"
    # [Rule] 공정 중(Producing/Consuming 팔레트 존재)일 때는 PROCESS
    elif any(s in ["Consuming", "Producing"] for s in pallet_statuses):
        lot.status = "PROCESS"
    # [Rule] 나머지는 WAIT (부분 생산/소비 후 비활성 상태 포함)
    else:
        lot.status = "WAIT"

    db.add(lot)
    # Note: caller should commit if needed, or we commit here for safety
    db.commit()
