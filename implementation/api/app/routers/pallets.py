"""팔레트 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.pallet import Pallet, PalletHistory
from app.core.socket import sio_server
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

from app.core.permissions import PermissionChecker
from app.models.user import User

router = APIRouter()


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
            # response_data["lot_number"] = lot.lot_number (Schema expects lot_number at root)
            response_data["lot_number"] = lot.lot_number
            if item:
                response_data["item_code"] = item.item_code
                response_data["item_name"] = item.item_name
                response_data["item_type"] = item.item_type
        
    if pallet.current_process:
        response_data["current_process_name"] = pallet.current_process.process_name
        
    return response_data


@router.post("", response_model=PalletResponse, status_code=201)
async def create_pallet(
    data: PalletCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("pallets", "write"))
):
    """팔레트 생성 (권한: pallets:write)"""
    existing = db.query(Pallet).filter(Pallet.pallet_no == data.pallet_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 팔레트 번호입니다")
    
    if data.rfid_epc:
        existing_epc = db.query(Pallet).filter(Pallet.rfid_epc == data.rfid_epc).first()
        if existing_epc:
            raise HTTPException(status_code=400, detail="이미 사용 중인 EPC입니다")
    
    pallet = Pallet(
        pallet_no=data.pallet_no,
        rfid_epc=data.rfid_epc,
        status="Empty",
        tag_status="AVAILABLE"
    )
    db.add(pallet)
    db.commit()
    db.refresh(pallet)
    
    await sio_server.emit('pallet_updated', {
        'pallet_id': pallet.id,
        'pallet_no': pallet.pallet_no,
        'status': pallet.status,
        'tag_status': pallet.tag_status
    })
    
    return _build_pallet_response(pallet, db)


@router.get("", response_model=PalletListResponse)
async def list_pallets(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("pallets", "read"))
):
    """팔레트 목록 조회 (권한: pallets:read)"""
    query = db.query(Pallet)
    if status:
        query = query.filter(Pallet.status == status)
    
    total = query.count()
    items = query.order_by(Pallet.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    responses = [_build_pallet_response(p, db) for p in items]
    
    return {
        "items": responses,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }


@router.get("/{id}", response_model=PalletResponse)
async def get_pallet(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("pallets", "read"))
):
    """팔레트 상세 조회 (권한: pallets:read)"""
    pallet = db.query(Pallet).filter(Pallet.id == id).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="팔레트를 찾을 수 없습니다")
    return _build_pallet_response(pallet, db)


@router.put("/{id}/tag-status", response_model=PalletResponse)
async def update_tag_status(
    id: int,
    data: PalletTagStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("pallets", "write"))
):
    """RFID 태그 상태 변경 (권한: pallets:write)"""
    pallet = db.query(Pallet).filter(Pallet.id == id).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="팔레트를 찾을 수 없습니다")
    
    pallet.tag_status = data.tag_status
    
    history = PalletHistory(
        pallet_id=pallet.id,
        lot_id=pallet.lot_id,
        process_id=pallet.current_process_id,
        previous_status=pallet.status,
        new_status=pallet.status,
        event_type="TAG_STATUS_CHANGE",
        scan_time=datetime.now(),
        worker_name="Admin",
        notes=f"Tag status changed to {data.tag_status}. Reason: {data.reason}"
    )
    
    db.add(history)
    db.commit()
    db.refresh(pallet)
    
    await sio_server.emit('pallet_updated', {
        'pallet_id': pallet.id,
        'pallet_no': pallet.pallet_no,
        'status': pallet.status,
        'tag_status': pallet.tag_status
    })
    
    return _build_pallet_response(pallet, db)


@router.put("/{id}/link-lot", response_model=PalletResponse)
async def link_lot(
    id: int, 
    data: PalletLinkLot,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("pallets", "write"))
):
    """팔레트에 LOT 연결 (권한: pallets:write)"""
    pallet = db.query(Pallet).filter(Pallet.id == id).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="팔레트를 찾을 수 없습니다")
        
    lot = db.query(Lot).filter(Lot.id == data.lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="LOT을 찾을 수 없습니다")

    # 기존 연결 해제? 덮어쓰기? 여기서는 덮어쓰기
    pallet.lot_id = lot.id
    pallet.status = "Stock"  # LOT 연결 시 재고 상태로 변경
    pallet.quantity = lot.quantity 

    db.commit()
    db.refresh(pallet)
    
    await sio_server.emit('pallet_updated', {
        'pallet_id': pallet.id,
        'pallet_no': pallet.pallet_no,
        'status': pallet.status,
        'tag_status': pallet.tag_status
    })
    
    return _build_pallet_response(pallet, db)


@router.put("/{id}/status", response_model=PalletResponse)
async def update_pallet_status(
    id: int,
    data: PalletStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("pallets", "write"))
):
    """팔레트 상태 강제 변경 (권한: pallets:write)"""
    pallet = db.query(Pallet).filter(Pallet.id == id).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="팔레트를 찾을 수 없습니다")
    
    previous_status = pallet.status
    pallet.status = data.status
    
    history = PalletHistory(
        pallet_id=pallet.id,
        lot_id=pallet.lot_id,
        process_id=pallet.current_process_id,
        previous_status=previous_status,
        new_status=data.status,
        event_type="FORCE_STATUS_CHANGE",
        scan_time=datetime.now(),
        worker_name="Admin",
        notes=f"Status changed to {data.status}. Reason: {data.reason}"
    )
    
    db.add(history)
    db.commit()
    db.refresh(pallet)
    
    await sio_server.emit('pallet_updated', {
        'pallet_id': pallet.id,
        'pallet_no': pallet.pallet_no,
        'status': pallet.status,
        'tag_status': pallet.tag_status
    })
    
    return _build_pallet_response(pallet, db)
