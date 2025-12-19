from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.services.rfid_service import RFIDService
from app.schemas.rfid import (
    ScanEvent, 
    BarcodeScanEvent,
    ScanResponse, 
    ReaderStatusEvent, 
    ReaderStatusResponse
)

from app.core.permissions import PermissionChecker
from app.models.user import User

router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
async def scan_tag(
    event: ScanEvent, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("rfid", "write"))
):
    """
    RFID 스캔 이벤트 처리 (권한: rfid:write)
    
    - EPC로 팔레트 조회
    - 포트로 공정/위치 식별
    - 상태 전이 처리
    - FIFO, 오투입 검증
    - 피드백 명령 반환
    """
    service = RFIDService(db)
    return await service.process_scan(event)


@router.post("/scan-barcode", response_model=ScanResponse)
async def scan_barcode(
    event: BarcodeScanEvent, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("rfid", "write"))
):
    """
    바코드 스캔 이벤트 처리 (RFID와 동일 로직) (권한: rfid:write)
    
    - Barcode(LOT번호)로 팔레트 조회
    - 이후 로직은 RFID 스캔과 동일
    """
    service = RFIDService(db)
    return await service.process_barcode_scan(event)


@router.post("/reader-status", response_model=ReaderStatusResponse)
async def reader_status(
    event: ReaderStatusEvent, 
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("rfid", "write"))
):
    """
    리더기 상태 수신 (Heartbeat) (권한: rfid:write)
    
    - 리더기 상태 로그 기록
    - 실시간 모니터링 업데이트용
    """
    service = RFIDService(db)
    return await service.update_reader_status(event)
