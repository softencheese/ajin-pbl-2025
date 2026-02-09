"""RFID 리더기 위치 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_admin_user
from app.models.rfid import RFIDReaderLocation
from app.schemas.reader_location import (
    ReaderLocationCreate,
    ReaderLocationUpdate,
    ReaderLocationResponse,
    ReaderLocationListResponse
)

from app.core.permissions import PermissionChecker
from app.models.user import User

router = APIRouter()


@router.get("", response_model=ReaderLocationListResponse)
async def list_reader_locations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_registered: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("reader_locations", "read"))
):
    """
    리더기 위치 목록 조회 (페이지네이션 지원) (권한: reader_locations:read)
    
    - is_registered=true: 공정 매핑된 리더기만
    - is_registered=false: 미등록(공정 미매핑) 리더기만
    - 파라미터 없음: 전체 조회
    """
    query = db.query(RFIDReaderLocation)
    
    if is_registered is True:
        query = query.filter(RFIDReaderLocation.process_id.isnot(None))
    elif is_registered is False:
        query = query.filter(RFIDReaderLocation.process_id.is_(None))
    
    total = query.count()
    locations = query.offset((page - 1) * per_page).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # Response 변환
    items = []
    for loc in locations:
        loc_dict = {
            "id": loc.id,
            "port_name": loc.port_name,
            "process_id": loc.process_id,
            "location_type": loc.location_type,
            "description": loc.description,
            "is_active": loc.is_active,
            "created_at": getattr(loc, "created_at", None),
            # "updated_at": getattr(loc, "updated_at", None), # TimestampSchema에 있다면
            
            "process_name": loc.process.process_name if loc.process else None,
            "process_code": loc.process.process_code if loc.process else None
        }
        items.append(ReaderLocationResponse(**loc_dict))

    return ReaderLocationListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/{id}", response_model=ReaderLocationResponse)
async def get_reader_location(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("reader_locations", "read"))
):
    """리더기 위치 상세 조회 (권한: reader_locations:read)"""
    location = db.query(RFIDReaderLocation).filter(
        RFIDReaderLocation.id == id
    ).first()
    if not location:
        raise HTTPException(status_code=404, detail="Reader location not found")
    return location


@router.get("/port/{port_name}", response_model=ReaderLocationResponse)
async def get_reader_location_by_port(
    port_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("reader_locations", "read"))
):
    """포트명으로 리더기 위치 조회 (권한: reader_locations:read)"""
    location = db.query(RFIDReaderLocation).filter(
        RFIDReaderLocation.port_name == port_name
    ).first()
    if not location:
        raise HTTPException(status_code=404, detail=f"Reader location not found for port: {port_name}")
    return location


@router.post("", response_model=ReaderLocationResponse, status_code=201)
async def create_reader_location(
    data: ReaderLocationCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("reader_locations", "write"))
):
    """리더기 위치 등록 (권한: reader_locations:write)"""
    existing = db.query(RFIDReaderLocation).filter(
        RFIDReaderLocation.port_name == data.port_name
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Port name already exists")
    
    location = RFIDReaderLocation(**data.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.put("/{id}", response_model=ReaderLocationResponse)
async def update_reader_location(
    id: int, 
    data: ReaderLocationUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("reader_locations", "write"))
):
    """리더기 위치 수정 (권한: reader_locations:write)"""
    location = db.query(RFIDReaderLocation).filter(
        RFIDReaderLocation.id == id
    ).first()
    if not location:
        raise HTTPException(status_code=404, detail="Reader location not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(location, key, value)
    
    db.commit()
    db.refresh(location)
    return location


@router.delete("/{id}")
async def delete_reader_location(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("reader_locations", "write"))
):
    """리더기 위치 삭제 (권한: reader_locations:write)"""
    location = db.query(RFIDReaderLocation).filter(
        RFIDReaderLocation.id == id
    ).first()
    if not location:
        raise HTTPException(status_code=404, detail="Reader location not found")
    
    db.delete(location)
    db.commit()
    return {"success": True, "message": "Reader location deleted"}


@router.put("/{id}/register", response_model=ReaderLocationResponse)
async def register_reader_location(
    id: int,
    data: ReaderLocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("reader_locations", "write"))
):
    """리더기 등록 (공정 매핑) (권한: reader_locations:write)"""
    location = db.query(RFIDReaderLocation).filter(
        RFIDReaderLocation.id == id
    ).first()
    if not location:
        raise HTTPException(status_code=404, detail="Reader location not found")

    # 공정 ID와 위치 타입은 필수
    if data.process_id is None or data.location_type is None:
         raise HTTPException(status_code=400, detail="Process ID and Location Type are required for registration")

    location.process_id = data.process_id
    location.location_type = data.location_type

    if data.description:
        location.description = data.description

    if data.is_active is not None:
        location.is_active = data.is_active

    db.commit()
    db.refresh(location)
    return location


@router.post("/test-connection")
async def test_reader_connection(
    data: dict,
    db: Session = Depends(get_db)
):
    """
    RFID 리더기 연결 테스트

    현재는 시뮬레이션 모드로, 실제 하드웨어 연결을 테스트하지 않고
    포트명 형식만 검증합니다.
    """
    port_name = data.get("port_name")
    if not port_name:
        raise HTTPException(status_code=400, detail="port_name is required")

    # 포트명 형식 검증
    import re

    # COM 포트 (Windows)
    if re.match(r'^COM\d+$', port_name):
        return {
            "success": True,
            "message": f"포트 {port_name}에 대한 연결 테스트가 성공했습니다 (시뮬레이션)",
            "data": {
                "port_name": port_name,
                "port_type": "COM (Windows Serial)",
                "status": "simulated_ok"
            }
        }

    # Unix 시리얼 포트
    elif re.match(r'^/dev/(tty|cu)\w+$', port_name):
        return {
            "success": True,
            "message": f"포트 {port_name}에 대한 연결 테스트가 성공했습니다 (시뮬레이션)",
            "data": {
                "port_name": port_name,
                "port_type": "Unix Serial",
                "status": "simulated_ok"
            }
        }

    # 네트워크 포트 (IP:PORT)
    elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$', port_name):
        return {
            "success": True,
            "message": f"포트 {port_name}에 대한 연결 테스트가 성공했습니다 (시뮬레이션)",
            "data": {
                "port_name": port_name,
                "port_type": "Network (TCP/IP)",
                "status": "simulated_ok"
            }
        }

    # 알 수 없는 포트 형식
    else:
        return {
            "success": True,
            "message": f"알 수 없는 포트 형식입니다. COM3, /dev/ttyUSB0, 또는 192.168.1.100:8080 형식을 사용하세요.",
            "data": {
                "port_name": port_name,
                "port_type": "Unknown",
                "status": "invalid_format"
            }
        }
