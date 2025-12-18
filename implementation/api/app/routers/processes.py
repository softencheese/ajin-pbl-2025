"""공정 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.process import Process
from app.schemas.process import (
    ProcessCreate,
    ProcessUpdate,
    ProcessResponse,
    ProcessOrderUpdate
)

router = APIRouter()


@router.get("")
async def list_processes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """공정 목록 조회 (페이지네이션 지원)"""
    query = db.query(Process).order_by(Process.process_order)
    
    total = query.count()
    processes = query.offset((page - 1) * per_page).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    return {
        "items": processes,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages
    }


@router.get("/{id}", response_model=ProcessResponse)
async def get_process(id: int, db: Session = Depends(get_db)):
    """공정 상세 조회"""
    process = db.query(Process).filter(Process.id == id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return process


@router.post("", response_model=ProcessResponse, status_code=201)
async def create_process(data: ProcessCreate, db: Session = Depends(get_db)):
    """공정 등록"""
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
async def update_process(id: int, data: ProcessUpdate, db: Session = Depends(get_db)):
    """공정 수정"""
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
    db: Session = Depends(get_db)
):
    """공정 순서 변경"""
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


@router.delete("/{id}")
async def delete_process(id: int, db: Session = Depends(get_db)):
    """공정 삭제 (사용 이력 없는 경우만)"""
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
