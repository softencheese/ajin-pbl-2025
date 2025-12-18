"""LOT 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
from app.database import get_db
from app.models.lot import Lot
from app.models.item import Item
from app.models.process import Process
from app.models.lot_genealogy import LotGenealogy
from app.schemas.lot import (
    LotCreate,
    LotReceiving,
    LotUpdate,
    LotStatusUpdate,
    LotResponse,
    LotListResponse
)

router = APIRouter()


def generate_lot_number(process_order: int, production_date: date, db: Session) -> str:
    """LOT 번호 자동 생성 (12자리 숫자)
    
    규칙: YYMMDD + PP + SSSS
    - YYMMDD: 생산일 (예: 251218)
    - PP: 공정 순서 (예: 00, 01, 02...)
    - SSSS: 일련번호 (0001~9999)
    """
    date_str = production_date.strftime("%y%m%d")
    proc_str = f"{process_order:02}"
    prefix = f"{date_str}{proc_str}"
    
    # 오늘 해당 공정에서 생성된 LOT 수 카운트
    pattern = f"{prefix}%"
    
    # 마지막 시퀀스 번호 조회 (더 안전한 방식)
    last_lot = db.query(Lot).filter(Lot.lot_number.like(pattern))\
        .order_by(Lot.lot_number.desc()).first()
    
    if last_lot:
        # 마지막 4자리 파싱
        try:
            last_seq = int(last_lot.lot_number[-4:])
            seq = last_seq + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
        
    return f"{prefix}{seq:04}"


@router.get("", response_model=LotListResponse)
async def list_lots(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    item_id: Optional[int] = None,
    item_type: Optional[str] = None,
    process_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """LOT 목록 조회"""
    query = db.query(Lot)
    
    if item_id:
        query = query.filter(Lot.item_id == item_id)
    if item_type:
        query = query.join(Item).filter(Item.item_type == item_type)
    if process_id:
        query = query.filter(Lot.process_id == process_id)
    if status:
        query = query.filter(Lot.status == status)
    if date_from:
        query = query.filter(Lot.production_date >= date_from)
    if date_to:
        query = query.filter(Lot.production_date <= date_to)
    
    total = query.count()
    items = query.order_by(Lot.production_date.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    # Response 변환
    lot_responses = []
    for lot in items:
        item = db.query(Item).filter(Item.id == lot.item_id).first()
        process = db.query(Process).filter(Process.id == lot.process_id).first() if lot.process_id else None
        
        lot_dict = {
            "id": lot.id,
            "lot_number": lot.lot_number,
            "barcode": lot.barcode,
            "item_id": lot.item_id,
            "quantity": lot.quantity,
            "initial_quantity": lot.initial_quantity,
            "status": lot.status,
            "production_date": lot.production_date,
            "process_id": lot.process_id,
            "supplier": lot.supplier,
            "worker_name": lot.worker_name,
            "qc_passed": lot.qc_passed,
            "notes": lot.notes,
            "created_at": lot.created_at,
            "updated_at": lot.updated_at,
            "item": {
                "id": item.id,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "item_type": item.item_type
            } if item else None,
            "process_name": process.process_name if process else None
        }
        lot_responses.append(LotResponse(**lot_dict))
    
    return LotListResponse(
        items=lot_responses,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.get("/{lot_id}", response_model=LotResponse)
async def get_lot(lot_id: int, db: Session = Depends(get_db)):
    """LOT 상세 조회"""
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="LOT을 찾을 수 없습니다")
    
    item = db.query(Item).filter(Item.id == lot.item_id).first()
    process = db.query(Process).filter(Process.id == lot.process_id).first() if lot.process_id else None
    
    return LotResponse(
        id=lot.id,
        lot_number=lot.lot_number,
        barcode=lot.barcode,
        item_id=lot.item_id,
        quantity=lot.quantity,
        initial_quantity=lot.initial_quantity,
        status=lot.status,
        production_date=lot.production_date,
        process_id=lot.process_id,
        supplier=lot.supplier,
        worker_name=lot.worker_name,
        qc_passed=lot.qc_passed,
        notes=lot.notes,
        created_at=lot.created_at,
        updated_at=lot.updated_at,
        item={
            "id": item.id,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_type": item.item_type
        } if item else None,
        process_name=process.process_name if process else None
    )


@router.post("/receiving", response_model=LotResponse, status_code=201)
async def create_receiving_lot(data: LotReceiving, db: Session = Depends(get_db)):
    """원자재 입고 LOT 생성 (RFID 불필요, 수동 등록)"""
    # 품목 검증 (RAW 타입만 허용)
    item = db.query(Item).filter(Item.id == data.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없습니다")
    if item.item_type != "RAW":
        raise HTTPException(status_code=422, detail="원자재 입고는 RAW 타입 품목만 가능합니다")
    
    # 입고 공정 찾기 (process_code = 'RECEIVING' 또는 process_order = 0)
    receiving_process = db.query(Process).filter(
        (Process.process_code == "RECEIVING") | (Process.process_order == 0)
    ).first()
    
    # LOT 번호 자동 생성 (입고 공정 순서 사용, 없으면 0)
    proc_order = receiving_process.process_order if receiving_process else 0
    lot_number = generate_lot_number(proc_order, data.production_date, db)
    
    lot = Lot(
        lot_number=lot_number,
        item_id=data.item_id,
        quantity=data.quantity,
        initial_quantity=data.quantity,
        status="STOCK",  # 원자재 입고는 바로 STOCK
        production_date=data.production_date,
        process_id=receiving_process.id if receiving_process else None,
        supplier=data.supplier or item.default_supplier,
        barcode=data.barcode or lot_number,
        notes=data.notes
    )
    
    db.add(lot)
    db.commit()
    db.refresh(lot)
    
    return LotResponse(
        id=lot.id,
        lot_number=lot.lot_number,
        barcode=lot.barcode,
        item_id=lot.item_id,
        quantity=lot.quantity,
        initial_quantity=lot.initial_quantity,
        status=lot.status,
        production_date=lot.production_date,
        process_id=lot.process_id,
        supplier=lot.supplier,
        worker_name=lot.worker_name,
        qc_passed=lot.qc_passed,
        notes=lot.notes,
        created_at=lot.created_at,
        updated_at=lot.updated_at,
        item={
            "id": item.id,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_type": item.item_type
        },
        process_name=None
    )


@router.post("", response_model=LotResponse, status_code=201)
async def create_lot(data: LotCreate, db: Session = Depends(get_db)):
    """생산 LOT 생성 (샤링, 프레스, 조립 등)"""
    # 품목 검증
    item = db.query(Item).filter(Item.id == data.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없습니다")
    
    # 공정 검증
    process = db.query(Process).filter(Process.id == data.process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="공정을 찾을 수 없습니다")
    
    # LOT 번호 자동 생성
    lot_number = generate_lot_number(process.process_order, data.production_date, db)
    
    lot = Lot(
        lot_number=lot_number,
        item_id=data.item_id,
        quantity=data.quantity,
        initial_quantity=data.quantity,
        status="STOCK",
        production_date=data.production_date,
        process_id=data.process_id,
        supplier=data.supplier,
        worker_name=data.worker_name,
        qc_passed=data.qc_passed,
        barcode=data.barcode or lot_number,
        notes=data.notes
    )
    
    db.add(lot)
    db.commit()
    db.refresh(lot)
    
    # 투입 LOT 정보가 있으면 lot_genealogy에 기록
    if data.input_lots:
        for input_info in data.input_lots:
            # 동시성 문제 방지를 위해 FOR UPDATE 락 사용
            input_lot = db.query(Lot).filter(
                Lot.id == input_info.lot_id
            ).with_for_update().first()
            
            if not input_lot:
                raise HTTPException(status_code=404, detail=f"투입 LOT {input_info.lot_id}를 찾을 수 없습니다")
            
            # 수량 부족 체크
            if input_lot.quantity < input_info.quantity_consumed:
                raise HTTPException(
                    status_code=400, 
                    detail=f"LOT {input_lot.lot_number}의 재고가 부족합니다. (현재: {input_lot.quantity}, 요청: {input_info.quantity_consumed})"
                )
            
            genealogy = LotGenealogy(
                input_lot_id=input_info.lot_id,
                output_lot_id=lot.id,
                process_id=data.process_id,
                quantity_consumed=input_info.quantity_consumed
            )
            db.add(genealogy)
            
            # 투입 LOT 수량 차감
            input_lot.quantity -= input_info.quantity_consumed
            if input_lot.quantity <= 0:
                input_lot.status = "CONSUMED"
        
        db.commit()
    
    return LotResponse(
        id=lot.id,
        lot_number=lot.lot_number,
        barcode=lot.barcode,
        item_id=lot.item_id,
        quantity=lot.quantity,
        initial_quantity=lot.initial_quantity,
        status=lot.status,
        production_date=lot.production_date,
        process_id=lot.process_id,
        supplier=lot.supplier,
        worker_name=lot.worker_name,
        qc_passed=lot.qc_passed,
        notes=lot.notes,
        created_at=lot.created_at,
        updated_at=lot.updated_at,
        item={
            "id": item.id,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_type": item.item_type
        },
        process_name=process.process_name
    )


@router.put("/{lot_id}/status")
async def update_lot_status(lot_id: int, data: LotStatusUpdate, db: Session = Depends(get_db)):
    """LOT 상태 변경"""
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="LOT을 찾을 수 없습니다")
    
    valid_statuses = ["WAIT", "PROCESS", "STOCK", "CONSUMED", "SHIPPED", "HOLD", "DEFECT"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 상태입니다. 가능한 값: {valid_statuses}")
    
    lot.status = data.status
    if data.notes:
        lot.notes = data.notes
    
    db.commit()
    db.refresh(lot)
    
    return {"success": True, "lot_number": lot.lot_number, "status": lot.status}


@router.put("/{lot_id}", response_model=LotResponse)
async def update_lot(lot_id: int, data: LotUpdate, db: Session = Depends(get_db)):
    """LOT 수정"""
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="LOT을 찾을 수 없습니다")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # 상태 변경 시 유효성 검사
    if "status" in update_data:
        valid_statuses = ["WAIT", "PROCESS", "STOCK", "CONSUMED", "SHIPPED", "HOLD", "DEFECT"]
        if update_data["status"] not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 상태입니다. 가능한 값: {valid_statuses}")
    
    for key, value in update_data.items():
        setattr(lot, key, value)
    
    db.commit()
    db.refresh(lot)
    
    item = db.query(Item).filter(Item.id == lot.item_id).first()
    process = db.query(Process).filter(Process.id == lot.process_id).first() if lot.process_id else None
    
    return LotResponse(
        id=lot.id,
        lot_number=lot.lot_number,
        barcode=lot.barcode,
        item_id=lot.item_id,
        quantity=lot.quantity,
        initial_quantity=lot.initial_quantity,
        status=lot.status,
        production_date=lot.production_date,
        process_id=lot.process_id,
        supplier=lot.supplier,
        worker_name=lot.worker_name,
        qc_passed=lot.qc_passed,
        notes=lot.notes,
        created_at=lot.created_at,
        updated_at=lot.updated_at,
        item={
            "id": item.id,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_type": item.item_type
        } if item else None,
        process_name=process.process_name if process else None
    )


@router.delete("/{lot_id}")
async def delete_lot(lot_id: int, db: Session = Depends(get_db)):
    """LOT 삭제 (참조되지 않은 경우만)"""
    from app.models.pallet import Pallet
    
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="LOT을 찾을 수 없습니다")
    
    # 팔레트 연결 확인
    pallet_count = db.query(Pallet).filter(Pallet.lot_id == lot_id).count()
    if pallet_count > 0:
        raise HTTPException(
            status_code=409, 
            detail=f"해당 LOT에 연결된 팔레트가 {pallet_count}개 있습니다. 삭제할 수 없습니다."
        )
    
    # lot_genealogy 참조 확인 (부모 또는 자식으로 사용된 경우)
    genealogy_count = db.query(LotGenealogy).filter(
        (LotGenealogy.input_lot_id == lot_id) | (LotGenealogy.output_lot_id == lot_id)
    ).count()
    if genealogy_count > 0:
        raise HTTPException(
            status_code=409, 
            detail=f"해당 LOT이 족보에서 {genealogy_count}번 참조됩니다. 삭제할 수 없습니다."
        )
    
    db.delete(lot)
    db.commit()
    return {"success": True, "message": "LOT이 삭제되었습니다"}
