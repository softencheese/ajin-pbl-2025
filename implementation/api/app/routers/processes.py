"""공정 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.deps import get_admin_user
from app.models.process import Process
from app.schemas.process import (
    ProcessCreate,
    ProcessUpdate,
    ProcessResponse,
    ProcessOrderUpdate,
    ProcessListResponse
)

from app.core.permissions import PermissionChecker
from app.models.user import User

router = APIRouter()


@router.get("", response_model=ProcessListResponse)
async def list_processes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("processes", "read"))
):
    """공정 목록 조회 (페이지네이션 지원) (권한: processes:read)"""
    query = db.query(Process).order_by(Process.process_order)
    
    total = query.count()
    processes = query.offset((page - 1) * per_page).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    return ProcessListResponse(
        items=[ProcessResponse.model_validate(p) for p in processes],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/connection-status", response_model=dict)
async def get_processes_connection_status(
    db: Session = Depends(get_db)
):
    """
    모든 공정의 RFID 리더기 연결 상태 조회

    반환 형식:
    {
        "1": {"connected": true, "active_readers": 2, "total_readers": 3},
        "2": {"connected": false, "active_readers": 0, "total_readers": 1},
        ...
    }
    """
    from app.models.rfid import RFIDReaderLocation

    processes = db.query(Process).all()
    status = {}

    for process in processes:
        # 해당 공정의 리더기 조회
        readers = db.query(RFIDReaderLocation).filter(
            RFIDReaderLocation.process_id == process.id
        ).all()

        total_readers = len(readers)
        active_readers = sum(1 for r in readers if r.is_active)

        # 활성화된 리더기가 1개 이상 있으면 연결됨으로 간주
        status[str(process.id)] = {
            "connected": active_readers > 0,
            "active_readers": active_readers,
            "total_readers": total_readers
        }

    return status


@router.get("/{id}", response_model=ProcessResponse)
async def get_process(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("processes", "read"))
):
    """공정 상세 조회 (권한: processes:read)"""
    process = db.query(Process).filter(Process.id == id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return process


@router.post("", response_model=ProcessResponse, status_code=201)
async def create_process(
    data: ProcessCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("processes", "write"))
):
    """공정 등록 (권한: processes:write)"""
    existing = db.query(Process).filter(
        Process.process_code == data.process_code
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Process code already exists")
    
    # 공정 순서 중복 체크
    order_exists = db.query(Process).filter(
        Process.process_order == data.process_order
    ).first()
    if order_exists:
        raise HTTPException(status_code=409, detail="Process order already exists")
    
    process = Process(**data.model_dump())
    db.add(process)
    db.commit()
    db.refresh(process)
    return process


@router.put("/{id}", response_model=ProcessResponse)
async def update_process(
    id: int, 
    data: ProcessUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("processes", "write"))
):
    """공정 수정 (권한: processes:write)"""
    process = db.query(Process).filter(Process.id == id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    # 공정 코드 변경 시 중복 체크
    if data.process_code and data.process_code != process.process_code:
        existing = db.query(Process).filter(
            Process.process_code == data.process_code
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Process code already exists")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(process, key, value)
    
    db.commit()
    db.refresh(process)
    return process

@router.put("/{id}/order", response_model=ProcessResponse)
async def update_process_order(
    id: int, 
    data: ProcessOrderUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("processes", "write"))
):
    """공정 순서 변경 (권한: processes:write)"""
    process = db.query(Process).filter(Process.id == id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    # 기존 순서와 새 순서 사이의 공정들 순서 조정
    old_order = process.process_order
    new_order = data.new_order
    
    if old_order < new_order:
        # 위로 이동: 사이에 있는 것들 순서 -1
        db.query(Process).filter(
            Process.process_order > old_order,
            Process.process_order <= new_order
        ).update({Process.process_order: Process.process_order - 1})
    else:
        # 아래로 이동: 사이에 있는 것들 순서 +1
        db.query(Process).filter(
            Process.process_order >= new_order,
            Process.process_order < old_order
        ).update({Process.process_order: Process.process_order + 1})
    
    process.process_order = new_order
    db.commit()
    db.refresh(process)
    return process


@router.get("/{id}/alive-lots")
async def get_process_alive_lots(
    id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("lots", "read"))
):
    """특정 공정의 활성 LOT 목록 조회 (CONSUMED, SHIPPED 제외) (권한: lots:read)"""
    from app.models.lot import Lot
    from app.models.item import Item
    
    # 공정 존재 확인
    process = db.query(Process).filter(Process.id == id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    # 활성 상태만 조회 (CONSUMED, SHIPPED, HOLD, DEFECT 제외)
    alive_statuses = ["WAIT", "PROCESS", "STOCK"]
    query = db.query(Lot).filter(
        Lot.process_id == id,
        Lot.status.in_(alive_statuses)
    )
    
    total = query.count()
    lots = query.order_by(Lot.production_date.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    # Response 변환
    lot_responses = []
    for lot in lots:
        item = db.query(Item).filter(Item.id == lot.item_id).first()
        
        lot_responses.append({
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
            "process_name": process.process_name
        })
    
    return {
        "items": lot_responses,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1,
        "process": {
            "id": process.id,
            "process_code": process.process_code,
            "process_name": process.process_name
        }
    }


@router.delete("/{id}")
async def delete_process(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("processes", "write"))
):
    """공정 삭제 (권한: processes:write)"""
    from app.models.rfid import RFIDReaderLocation
    from app.models.lot import Lot
    
    process = db.query(Process).filter(Process.id == id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    # 연결된 리더기 확인
    reader_count = db.query(RFIDReaderLocation).filter(
        RFIDReaderLocation.process_id == id
    ).count()
    if reader_count > 0:
        raise HTTPException(
            status_code=409, 
            detail=f"해당 공정에 연결된 리더기가 {reader_count}개 있습니다. 먼저 리더기 매핑을 해제하세요."
        )
    
    # 연결된 LOT 확인
    lot_count = db.query(Lot).filter(Lot.process_id == id).count()
    if lot_count > 0:
        raise HTTPException(
            status_code=409, 
            detail=f"해당 공정에서 생성된 LOT가 {lot_count}개 있습니다. 삭제할 수 없습니다."
        )
    
    # 삭제 후 순서 재정렬
    deleted_order = process.process_order
    db.delete(process)
    
    # 삭제된 순서 이후의 공정들 순서 -1
    db.query(Process).filter(
        Process.process_order > deleted_order
    ).update({Process.process_order: Process.process_order - 1})
    
    db.commit()
    return {"success": True, "message": "공정이 삭제되었습니다"}

