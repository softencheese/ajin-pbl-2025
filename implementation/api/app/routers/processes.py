"""공정 관리 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.process import Process
from app.schemas.process import (
    ProcessCreate,
    ProcessResponse,
    ProcessOrderUpdate
)

router = APIRouter()


@router.get("", response_model=List[ProcessResponse])
async def list_processes(db: Session = Depends(get_db)):
    """공정 목록 조회 (순서대로)"""
    processes = db.query(Process).order_by(Process.process_order).all()
    return processes


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
