"""팔레트 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.pallet import Pallet, PalletHistory
from app.models.lot import Lot
from app.models.assembly import AssemblyLot
from app.schemas.pallet import (
    PalletCreate,
    PalletResponse,
    PalletListResponse,
    PalletLinkLot,
    PalletStatusUpdate
)

router = APIRouter()


@router.get("", response_model=PalletListResponse)
async def list_pallets(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    process_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """팔레트 목록 조회"""
    query = db.query(Pallet)
    
    if status:
        query = query.filter(Pallet.status == status)
    if process_id:
        query = query.filter(Pallet.current_process_id == process_id)
    if search:
        query = query.filter(
            Pallet.pallet_no.contains(search) |
            Pallet.rfid_epc.contains(search)
        )
    
    total = query.count()
    pallets = query.offset((page - 1) * per_page).limit(per_page).all()
    
    items = []
    for pallet in pallets:
        item = _build_pallet_response(pallet)
        items.append(item)
    
    return PalletListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.get("/{pallet_no}", response_model=PalletResponse)
async def get_pallet(pallet_no: str, db: Session = Depends(get_db)):
    """팔레트 상세 조회"""
    pallet = db.query(Pallet).filter(Pallet.pallet_no == pallet_no).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="Pallet not found")
    
    return _build_pallet_response(pallet)


@router.post("", response_model=PalletResponse, status_code=201)
async def create_pallet(data: PalletCreate, db: Session = Depends(get_db)):
    """팔레트 생성"""
    # 팔레트 번호 중복 체크
    existing = db.query(Pallet).filter(
        Pallet.pallet_no == data.pallet_no
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Pallet number already exists")
    
    # EPC 중복 체크
    if data.rfid_epc:
        epc_exists = db.query(Pallet).filter(
            Pallet.rfid_epc == data.rfid_epc
        ).first()
        if epc_exists:
            raise HTTPException(status_code=409, detail="RFID EPC already in use")
    
    pallet = Pallet(
        pallet_no=data.pallet_no,
        rfid_epc=data.rfid_epc,
        status="Generated"
    )
    
    db.add(pallet)
    db.commit()
    db.refresh(pallet)
    
    return _build_pallet_response(pallet)


@router.put("/{pallet_no}/link-lot", response_model=PalletResponse)
async def link_lot(
    pallet_no: str, 
    data: PalletLinkLot, 
    db: Session = Depends(get_db)
):
    """팔레트에 LOT 연결"""
    pallet = db.query(Pallet).filter(Pallet.pallet_no == pallet_no).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="Pallet not found")
    
    if data.lot_id:
        lot = db.query(Lot).filter(Lot.id == data.lot_id).first()
        if not lot:
            raise HTTPException(status_code=404, detail="Lot not found")
        pallet.lot_id = data.lot_id
        pallet.assembly_lot_id = None
    elif data.assembly_lot_id:
        assembly_lot = db.query(AssemblyLot).filter(
            AssemblyLot.id == data.assembly_lot_id
        ).first()
        if not assembly_lot:
            raise HTTPException(status_code=404, detail="Assembly lot not found")
        pallet.assembly_lot_id = data.assembly_lot_id
        pallet.lot_id = None
    
    # 상태를 Empty로 변경 (태그 매칭 완료)
    if pallet.status == "Generated":
        pallet.status = "Empty"
    
    db.commit()
    db.refresh(pallet)
    
    return _build_pallet_response(pallet)


@router.put("/{pallet_no}/status", response_model=PalletResponse)
async def update_status(
    pallet_no: str, 
    data: PalletStatusUpdate, 
    db: Session = Depends(get_db)
):
    """팔레트 상태 강제 변경 (관리자)"""
    pallet = db.query(Pallet).filter(Pallet.pallet_no == pallet_no).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="Pallet not found")
    
    previous_status = pallet.status
    pallet.status = data.status
    
    # 이력 기록
    history = PalletHistory(
        pallet_id=pallet.id,
        lot_id=pallet.lot_id,
        assembly_lot_id=pallet.assembly_lot_id,
        process_id=pallet.current_process_id,
        previous_status=previous_status,
        current_status=data.status,
        event_type="ADMIN_STATUS_CHANGE",
        worker_name="Admin"  # TODO: 실제 관리자 정보
    )
    
    db.add(history)
    db.commit()
    db.refresh(pallet)
    
    return _build_pallet_response(pallet)


def _build_pallet_response(pallet: Pallet) -> dict:
    """팔레트 응답 데이터 구성"""
    response_data = {
        "id": pallet.id,
        "pallet_no": pallet.pallet_no,
        "rfid_epc": pallet.rfid_epc,
        "status": pallet.status,
        "quantity": pallet.quantity,
        "created_at": pallet.created_at,
        "updated_at": getattr(pallet, 'updated_at', None),
    }
    
    if pallet.lot:
        response_data["lot_no"] = pallet.lot.lot_no
        response_data["part_number"] = pallet.lot.part.part_number
        response_data["part_name"] = pallet.lot.part.part_name
    elif pallet.assembly_lot:
        response_data["lot_no"] = pallet.assembly_lot.lot_no
        response_data["part_number"] = pallet.assembly_lot.part.part_number
        response_data["part_name"] = pallet.assembly_lot.part.part_name
        
    if pallet.current_process:
        response_data["current_process_name"] = pallet.current_process.process_name
        
    return response_data
