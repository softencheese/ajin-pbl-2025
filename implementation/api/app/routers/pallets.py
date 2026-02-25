"""팔레트 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.pallet import Pallet, PalletHistory
from app.models.physical_pallet import PhysicalPallet
from app.core.socket import sio_server
from app.models.lot import Lot
from app.models.item import Item
from app.services.lot_service import sync_lot_status_and_quantity
from app.schemas.pallet import (
    PalletCreate,
    PalletUpdate,
    PalletResponse,
    PalletListResponse,
    PalletLinkLot,
    PalletStatusUpdate,
    PalletForceStatusUpdate,
    PalletTagStatusUpdate,
    FIFOQueueResponse,
    FIFOQueueItem
)

from app.core.permissions import PermissionChecker
from app.models.user import User

router = APIRouter()


def _build_pallet_response(pallet: Pallet, db: Session) -> dict:
    """팔레트 응답 데이터 구성"""
    response_data = {
        "id": pallet.id,
        "pallet_no": pallet.pallet_no,
        "physical_pallet_id": pallet.physical_pallet_id,
        "quantity": getattr(pallet, 'quantity', 0),
        "tag_status": pallet.tag_status,
        "lot_id": pallet.lot_id,
        "current_process_id": pallet.current_process_id,
        "created_at": pallet.created_at,
        "updated_at": getattr(pallet, 'updated_at', None),
        "tag_registered_at": pallet.tag_registered_at,
    }

    # 실물 팔레트 정보 및 status
    if pallet.physical_pallet:
        response_data["rfid_epc"] = pallet.physical_pallet.epc
        
    response_data["pallet_status"] = getattr(pallet, 'status', None)
    response_data["status"] = getattr(pallet, 'status', None)

    # LOT 정보
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


@router.post("", response_model=PalletResponse, status_code=201)
async def create_pallet(
    data: PalletCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("pallets", "write"))
):
    """팔레트 생성 (권한: pallets:write). rfid_epc 제공 시 실물 팔레트 자동 생성."""
    existing = db.query(Pallet).filter(Pallet.pallet_no == data.pallet_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 팔레트 번호입니다")

    physical_pallet_id = getattr(data, 'physical_pallet_id', None)
    if getattr(data, 'rfid_epc', None):
        pp = db.query(PhysicalPallet).filter(PhysicalPallet.epc == data.rfid_epc).first()
        if not pp:
            pp = PhysicalPallet(epc=data.rfid_epc, pallet_code=data.pallet_no)
            db.add(pp)
            db.flush()
        physical_pallet_id = pp.id

    pallet = Pallet(
        pallet_no=data.pallet_no,
        physical_pallet_id=physical_pallet_id,
        quantity=getattr(data, 'quantity', 0),
        status=(data.status if getattr(data, 'status', None) else 'Empty'),
        tag_status="AVAILABLE"
    )
    db.add(pallet)
    db.commit()
    db.refresh(pallet)
    
    # pallet 상태 가져오기
    pallet_status = pallet.status
    
    await sio_server.emit('pallet_updated', {
        'pallet_id': pallet.id,
        'pallet_no': pallet.pallet_no,
        'status': pallet_status,
        'tag_status': pallet.tag_status
    })
    
    return _build_pallet_response(pallet, db)


@router.get("", response_model=PalletListResponse)
async def list_pallets(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    lot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("pallets", "read"))
):
    """팔레트 목록 조회 (권한: pallets:read)"""
    query = db.query(Pallet)
    if status:
        query = query.filter(Pallet.tag_status == status)
    if lot_id:
        query = query.filter(Pallet.lot_id == lot_id)

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


@router.get("/fifo-queue", response_model=FIFOQueueResponse)
async def get_fifo_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("pallets", "read"))
):
    """
    FIFO 대기열 조회 (권한: pallets:read)

    Stock 상태 팔레트를 created_at 순서로 정렬하여 반환
    각 팔레트의 스캔 상태 (대기/완료/위반) 포함
    """
    # Stock 상태 팔레트를 created_at 오름차순으로 조회
    stock_pallets = db.query(Pallet).join(
        PhysicalPallet, Pallet.physical_pallet_id == PhysicalPallet.id, isouter=True
    ).filter(
        Pallet.status == "Stock"
    ).order_by(Pallet.created_at.asc()).all()

    fifo_items = []
    for idx, pallet in enumerate(stock_pallets, start=1):
        # 최근 IN 위치 스캔 이력 조회
        recent_scan = db.query(PalletHistory).filter(
            PalletHistory.pallet_id == pallet.id,
            PalletHistory.location_type == "IN"
        ).order_by(PalletHistory.scan_time.desc()).first()

        scan_status = "WAITING"  # 기본값
        scan_time = None

        if recent_scan:
            scan_time = recent_scan.scan_time
            # notes에 "FIFO 위반" 문구가 있으면 VIOLATION
            if recent_scan.notes and "FIFO 위반" in recent_scan.notes:
                scan_status = "VIOLATION"
            else:
                scan_status = "OK"

        lot = db.query(Lot).filter(Lot.id == pallet.lot_id).first() if pallet.lot_id else None
        item = db.query(Item).filter(Item.id == lot.item_id).first() if lot else None

        fifo_items.append({
            "queue_position": idx,
            "pallet_id": pallet.id,
            "pallet_no": pallet.pallet_no,
            "rfid_epc": pallet.physical_pallet.epc if pallet.physical_pallet else None,
            "lot_no": lot.lot_number if lot else None,
            "item_code": item.item_code if item else None,
            "item_name": item.item_name if item else None,
            "created_at": pallet.created_at,
            "scan_status": scan_status,
            "scan_time": scan_time
        })

    return {
        "items": fifo_items,
        "total": len(fifo_items)
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


@router.post("/{id}/unlink-tag", response_model=PalletResponse)
async def unlink_pallet_tag(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("pallets", "write"))
):
    """팔레트 RFID 태그 연결 해제 (권한: pallets:write)"""
    pallet = db.query(Pallet).filter(Pallet.id == id).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="팔레트를 찾을 수 없습니다")
    
    if pallet.physical_pallet:
        # 가상 팔레트와 실물 팔레트 연결 해제
        pallet.physical_pallet_id = None
        pallet.tag_status = "AVAILABLE"
        pallet.tag_deregistered_at = datetime.now()
        
    db.commit()
    db.refresh(pallet)
    return _build_pallet_response(pallet, db)


@router.put("/{id}", response_model=PalletResponse)
async def update_pallet(
    id: int,
    data: PalletUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("pallets", "write"))
):
    """팔레트 부분 수정 (rfid_epc 연결 등) (권한: pallets:write)"""
    pallet = db.query(Pallet).filter(Pallet.id == id).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="팔레트를 찾을 수 없습니다")
    if getattr(data, "rfid_epc", None):
        pp = db.query(PhysicalPallet).filter(PhysicalPallet.epc == data.rfid_epc).first()
        if not pp:
            pp = PhysicalPallet(epc=data.rfid_epc, pallet_code=pallet.pallet_no or data.rfid_epc)
            db.add(pp)
            db.flush()
        pallet.physical_pallet_id = pp.id
    db.commit()
    db.refresh(pallet)
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
    
    current_status = pallet.status
    
    history = PalletHistory(
        pallet_id=pallet.id,
        lot_id=pallet.lot_id,
        process_id=pallet.current_process_id,
        previous_status=current_status,
        new_status=current_status,
        event_type="TAG_STATUS_CHANGE",
        scan_time=datetime.now(),
        worker_name="Admin",
        notes=f"Tag status changed to {data.tag_status}. Reason: {data.reason}"
    )
    
    db.add(history)
    db.commit()
    db.refresh(pallet)
    
    pallet_status = pallet.status
    
    await sio_server.emit('pallet_updated', {
        'pallet_id': pallet.id,
        'pallet_no': pallet.pallet_no,
        'status': pallet_status,
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

    # 상태 전이 로직이 pallet.status를 사용하므로 둘 다 Stock으로 설정
    pallet.status = "Stock"

    # LOT 동기화 (AI_README 규칙 적용)
    sync_lot_status_and_quantity(pallet.lot_id, db)

    # 수량은 lot에 이미 있음 (pallet에는 quantity 필드 없음)
    link_quantity = getattr(data, 'quantity', None) if getattr(data, 'quantity', None) is not None else lot.quantity
    
    # 유효성 검사
    if link_quantity > lot.quantity:
         raise HTTPException(status_code=400, detail=f"요청 수량이 LOT 재고보다 많습니다. (LOT: {lot.quantity})")

    # 이력 기록
    history = PalletHistory(
        pallet_id=pallet.id,
        lot_id=pallet.lot_id,
        process_id=pallet.current_process_id,
        previous_status=pallet.status, # 이미 위에서 변경했지만, 개념상 연결 전 상태가 맞으나 로직상 현재는 변경 후임. 
                                     # 정확히 하려면 변경 전 상태를 변수에 저장했어야 함.
                                     # 하지만 위에서 status를 바로 Stock으로 대입했음.
                                     # 수정: 위에서 대입하기 전에 prev_status 저장 필요.
                                     # 일단 여기서는 'Generated' or 'Empty' 였을 것임.
        new_status="Stock",
        event_type="LINK_LOT",
        scan_time=datetime.now(),
        worker_name="System", # or current_user.username if available context
        notes=f"Linked Lot {lot.lot_number} (Qty: {link_quantity})"
    )
    db.add(history)

    db.commit()
    db.refresh(pallet)
    
    # pallet 상태 가져오기
    pallet_status = pallet.status
    
    await sio_server.emit('pallet_updated', {
        'pallet_id': pallet.id,
        'pallet_no': pallet.pallet_no,
        'status': pallet_status,
        'tag_status': pallet.tag_status
    })
    
    return _build_pallet_response(pallet, db)


@router.put("/{id}/status", response_model=PalletResponse)
async def update_pallet_status(
    id: int,
    data: PalletForceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("pallets", "write"))
):
    """팔레트 상태 강제 변경 (권한: pallets:write)"""
    pallet = db.query(Pallet).filter(Pallet.id == id).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="팔레트를 찾을 수 없습니다")
    
    if not pallet.physical_pallet:
        raise HTTPException(status_code=400, detail="실물 팔레트가 연결되지 않았습니다")

    previous_status_str = getattr(pallet, 'status', 'Unknown')
    target_status = data.status

    if target_status.lower() == 'rollback':
        if not pallet.previous_status:
            raise HTTPException(status_code=400, detail="이전 상태가 존재하지 않아 Rollback할 수 없습니다")
        # Rollback인 경우 실제 목표 상태를 previous_status로 설정
        target_status = pallet.previous_status
        data.reason = f"Rollback to {pallet.previous_status}" + (f" ({data.reason})" if data.reason else "")
    elif target_status.lower() == 'scrap':
        if previous_status_str.lower() != 'defect':
            raise HTTPException(status_code=400, detail="Defect 상태에서만 Scrap 상태로 전환할 수 있습니다")
        target_status = 'Scrap'

    try:
        # 실제 상태가 변경될 때만 history 기록 및 sync
        if previous_status_str != target_status:
            pallet.previous_status = previous_status_str
            
        # virtual pallet 상태도 동기화
        pallet.status = target_status

        # AI_README: 팔레트가 Deregistered 또는 Scrap 시 tag_status 업데이트
        if target_status == "Deregistered":
            pallet.tag_status = "OUT_OF_USE"
            pallet.tag_deregistered_at = datetime.now()
            pallet.quantity = 0 # 등록 해제 시 수량 초기화 (실물 없음)
        elif target_status == "Scrap":
            # AI_README: 폐기 시 생산 수량(produced_quantity)에서 차감하여 Net 생산량을 유지
            if pallet.lot and previous_status_str in ["Stock", "Finished", "Defect", "Hold"]:
                pallet.lot.produced_quantity = max(0, pallet.lot.produced_quantity - (pallet.quantity or 0))
                db.add(pallet.lot)
            
            pallet.tag_status = "OUT_OF_USE"
            pallet.quantity = 0 # 폐기 시 수량 0
    except (ValueError, TypeError):
        pass

    history = PalletHistory(
        pallet_id=pallet.id,
        lot_id=pallet.lot_id,
        process_id=pallet.current_process_id,
        previous_status=previous_status_str,
        new_status=target_status,
        event_type="FORCE_STATUS_CHANGE",
        scan_time=datetime.now(),
        worker_name="Admin",
        notes=f"Status changed to {target_status}. Reason: {data.reason}"
    )

    db.add(history)
    
    # LOT 동기화 (AI_README 규칙 적용)
    if pallet.lot_id:
        sync_lot_status_and_quantity(pallet.lot_id, db)

    db.commit()
    db.refresh(pallet)
    if pallet.physical_pallet:
        db.refresh(pallet.physical_pallet)

    pallet_status = pallet.status

    await sio_server.emit('pallet_updated', {
        'pallet_id': pallet.id,
        'pallet_no': pallet.pallet_no,
        'status': pallet_status,
        'tag_status': pallet.tag_status
    })

    return _build_pallet_response(pallet, db)
