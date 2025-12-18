from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ReaderInfo(BaseModel):
    """RFID 리더기 정보"""
    model: Optional[str] = Field(None, description="리더기 모델명")
    antenna: int = Field(default=1, description="안테나 번호")
    rssi: Optional[int] = Field(None, description="신호 세기")



class ScanEvent(BaseModel):
    """RFID 스캔 이벤트"""
    epc: str = Field(..., description="RFID Tag EPC")
    port_name: str = Field(..., description="Reader Port Name (COM3, READER_01)")
    scan_time: datetime = Field(default_factory=datetime.now, description="스캔 시각")
    reader_info: Optional[ReaderInfo] = Field(None, description="리더기 상세 정보")


class BarcodeScanEvent(BaseModel):
    """바코드 스캔 이벤트"""
    barcode: str = Field(..., description="Barcode (LOT Number)")
    port_name: str = Field(..., description="Reader Port Name")
    scan_time: datetime = Field(default_factory=datetime.now, description="스캔 시각")
    reader_info: Optional[ReaderInfo] = Field(None, description="리더기 상세 정보")


class ReaderStatusEvent(BaseModel):
    """리더기 상태 이벤트 (Heartbeat)"""
    port_name: str = Field(..., description="리더기 포트")
    status: str = Field(..., description="상태 (CONNECTED, DISCONNECTED, ERROR)")
    last_scan_time: Optional[datetime] = Field(None, description="마지막 스캔 시각")
    uptime_seconds: int = Field(default=0, description="가동 시간 (초)")
    total_scans: int = Field(default=0, description="총 스캔 횟수")
    error_count: int = Field(default=0, description="에러 횟수")


class Feedback(BaseModel):
    """피드백 명령 (부저, LED)"""
    action: str = Field(default="BUZZER", description="액션 타입 (BUZZER, LED)")
    pattern: str = Field(..., description="패턴 (SUCCESS, WARNING, ERROR)")
    count: int = Field(default=1, description="반복 횟수")
    led_color: str = Field(..., description="LED 색상 (GREEN, YELLOW, RED)")


class FIFOWarning(BaseModel):
    """FIFO 위반 경고 정보"""
    type: str = Field(default="FIFO_VIOLATION")
    message: str = Field(..., description="경고 메시지")
    oldest_stock: Optional[Dict[str, Any]] = Field(None, description="더 오래된 재고 정보")


class ScanError(BaseModel):
    """스캔 오류 정보"""
    type: str = Field(..., description="오류 타입 (WRONG_PART, UNKNOWN_PORT, PALLET_NOT_FOUND)")
    message: str = Field(..., description="오류 메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="상세 정보")


class PalletInfo(BaseModel):
    """팔레트 정보 (스캔 응답용)"""
    pallet_no: str
    previous_status: str
    current_status: str
    lot_no: Optional[str] = None
    part_number: Optional[str] = None
    part_name: Optional[str] = None


class ScanResponse(BaseModel):
    """RFID 스캔 응답"""
    success: bool
    pallet: Optional[PalletInfo] = None
    error: Optional[ScanError] = None
    warning: Optional[FIFOWarning] = None
    feedback: Feedback


class ReaderStatusResponse(BaseModel):
    """리더기 상태 응답"""
    success: bool
    message: str
