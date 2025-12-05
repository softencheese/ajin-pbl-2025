"""RFID 태그 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.rfid import RFIDTag
from app.models.pallet import Pallet
from app.schemas.rfid_tag import (
    RFIDTagCreate,
    RFIDTagResponse,
    RFIDTagListResponse,
    RFIDTagStatusUpdate
)

router = APIRouter()


@router.get("", response_model=RFIDTagListResponse)
async def list_rfid_tags(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="AVAILABLE, IN_USE, DAMAGED"),
    db: Session = Depends(get_db)
):
    """RFID 태그 목록 조회"""
    query = db.query(RFIDTag)
    
    if status:
        query = query.filter(RFIDTag.status == status)
    
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return RFIDTagListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.get("/{id}", response_model=RFIDTagResponse)
async def get_rfid_tag(id: int, db: Session = Depends(get_db)):
    """RFID 태그 상세 조회"""
    tag = db.query(RFIDTag).filter(RFIDTag.id == id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="RFID tag not found")
    return tag


@router.post("", response_model=RFIDTagResponse, status_code=201)
async def create_rfid_tag(data: RFIDTagCreate, db: Session = Depends(get_db)):
    """RFID 태그 등록"""
    # EPC 중복 체크
    existing = db.query(RFIDTag).filter(RFIDTag.epc == data.epc).first()
    if existing:
        raise HTTPException(status_code=409, detail="EPC already exists")
    
    tag = RFIDTag(
        epc=data.epc,
        status="AVAILABLE"
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/{id}/status", response_model=RFIDTagResponse)
async def update_rfid_tag_status(
    id: int, 
    data: RFIDTagStatusUpdate, 
    db: Session = Depends(get_db)
):
    """RFID 태그 상태 변경"""
    tag = db.query(RFIDTag).filter(RFIDTag.id == id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="RFID tag not found")
    
    # 유효한 상태인지 확인
    valid_statuses = ["AVAILABLE", "IN_USE", "DAMAGED"]
    if data.status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    tag.status = data.status
    db.commit()
    db.refresh(tag)
    return tag


@router.post("/{id}/detach")
async def detach_rfid_tag(id: int, db: Session = Depends(get_db)):
    """
    RFID 태그 팔레트 연결 해제
    
    태그와 연결된 팔레트의 rfid_epc를 NULL로 설정하고
    태그 상태를 AVAILABLE로 변경합니다.
    """
    tag = db.query(RFIDTag).filter(RFIDTag.id == id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="RFID tag not found")
    
    # 연결된 팔레트 찾기
    pallet = db.query(Pallet).filter(Pallet.rfid_epc == tag.epc).first()
    
    if pallet:
        pallet.rfid_epc = None
        pallet.status = "Deregistered"
    
    tag.status = "AVAILABLE"
    tag.current_pallet_id = None
    
    db.commit()
    
    return {
        "success": True, 
        "message": "RFID tag detached from pallet",
        "pallet_no": pallet.pallet_no if pallet else None
    }


@router.delete("/{id}")
async def delete_rfid_tag(id: int, db: Session = Depends(get_db)):
    """RFID 태그 삭제 (사용 중이 아닌 경우만)"""
    tag = db.query(RFIDTag).filter(RFIDTag.id == id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="RFID tag not found")
    
    if tag.status == "IN_USE":
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete tag that is in use. Detach first."
        )
    
    db.delete(tag)
    db.commit()
    return {"success": True, "message": "RFID tag deleted"}
