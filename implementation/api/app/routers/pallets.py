"""팔레트 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.pallet import Pallet, PalletHistory
from app.models.lot import Lot
from app.models.item import Item
from app.schemas.pallet import (
    PalletCreate,
    PalletResponse,
    PalletListResponse,
    PalletLinkLot,
    PalletStatusUpdate,
    PalletTagStatusUpdate
)

router = APIRouter()

# ... (omitted existing code)

@router.put("/{pallet_no}/tag-status", response_model=PalletResponse)
async def update_tag_status(
    pallet_no: str,
    data: PalletTagStatusUpdate,
    db: Session = Depends(get_db)
):
    """RFID 태그 상태 변경"""
    pallet = db.query(Pallet).filter(Pallet.pallet_no == pallet_no).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="팔레트를 찾을 수 없습니다")
    
    pallet.tag_status = data.tag_status
    
    # 이력 기록 (선택 사항: 태그 상태 변경도 이력에 남길지 결정 필요, 여기서는 남김)
    history = PalletHistory(
        pallet_id=pallet.id,
        lot_id=pallet.lot_id,
        process_id=pallet.current_process_id,
        previous_status=pallet.status, # 팔레트 상태는 유지
        new_status=pallet.status,
        event_type="TAG_STATUS_CHANGE",
        scan_time=datetime.now(),
        worker_name="Admin",
        notes=f"Tag status changed to {data.tag_status}. Reason: {data.reason}"
    )
    
    db.add(history)
    db.commit()
    db.refresh(pallet)
    
    return _build_pallet_response(pallet, db)


# ... (omitted update_status)

def _build_pallet_response(pallet: Pallet, db: Session) -> dict:
    """팔레트 응답 데이터 구성"""
    response_data = {
        "id": pallet.id,
        "pallet_no": pallet.pallet_no,
        "rfid_epc": pallet.rfid_epc,
        "status": pallet.status,
        "tag_status": pallet.tag_status,
        "quantity": pallet.quantity,
        "created_at": pallet.created_at,
        "updated_at": getattr(pallet, 'updated_at', None),
    }
    
    if pallet.lot_id:
        lot = db.query(Lot).filter(Lot.id == pallet.lot_id).first()
        if lot:
            item = db.query(Item).filter(Item.id == lot.item_id).first()
            response_data["lot_number"] = lot.lot_number
            if item:
                response_data["item_code"] = item.item_code
                response_data["item_name"] = item.item_name
                response_data["item_type"] = item.item_type
        
    if pallet.current_process:
        response_data["current_process_name"] = pallet.current_process.process_name
        
    return response_data
