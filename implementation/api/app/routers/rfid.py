from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.rfid_service import RFIDService
from app.schemas.rfid import (
    ScanEvent, 
    ScanResponse, 
    ReaderStatusEvent, 
    ReaderStatusResponse
)

router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
async def scan_tag(event: ScanEvent, db: Session = Depends(get_db)):
    """
    RFID 스캔 이벤트 처리
    
    - EPC로 팔레트 조회
    - 포트로 공정/위치 식별
    - 상태 전이 처리
    - FIFO, 오투입 검증
    - 피드백 명령 반환
    """
    service = RFIDService(db)
    return await service.process_scan(event)


@router.post("/reader-status", response_model=ReaderStatusResponse)
async def reader_status(event: ReaderStatusEvent, db: Session = Depends(get_db)):
    """
    리더기 상태 수신 (Heartbeat)
    
    - 리더기 상태 로그 기록
    - 실시간 모니터링 업데이트용
    """
    service = RFIDService(db)
    return await service.update_reader_status(event)
