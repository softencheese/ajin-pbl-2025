"""팔레트 스키마"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class PalletBase(BaseModel):
    pallet_no: str = Field(..., description="팔레트 번호")
    physical_pallet_id: Optional[int] = Field(None, description="실물 팔레트 ID")
    quantity: Optional[int] = Field(default=0, description="현재 적재 수량")


class PalletCreate(PalletBase):
    """팔레트 생성 시 rfid_epc 제공 시 실물 팔레트 자동 생성"""
    rfid_epc: Optional[str] = Field(None, description="RFID EPC (제공 시 PhysicalPallet 생성 후 연결)")
    status: Optional[str] = Field(None, description="초기 상태 (Empty, Stock 등)")


class PalletUpdate(BaseModel):
    """팔레트 부분 수정 (rfid_epc 연결 등)"""
    rfid_epc: Optional[str] = Field(None, description="RFID EPC (기존 PhysicalPallet 연결 또는 새로 생성)")


class PalletResponse(BaseModel):
    id: int
    pallet_no: str
    physical_pallet_id: Optional[int] = None
    quantity: int = Field(default=0, description="현재 적재 수량")
    tag_status: str = Field(default="AVAILABLE", description="RFID 태그 상태 (AVAILABLE, IN_USE, DAMAGED)")
    lot_id: Optional[int] = Field(None, description="연결된 LOT ID")
    current_process_id: Optional[int] = Field(None, description="현재 공정 ID")
    tag_registered_at: Optional[datetime] = None
    tag_deregistered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # 연관 정보 (간접 제공)
    rfid_epc: Optional[str] = None  # physical_pallet.rfid_epc
    status: Optional[str] = None  # pallet.status 또는 physical_pallet.status
    pallet_status: Optional[str] = None  # physical_pallet.status (별칭)
    lot_number: Optional[str] = None
    item_code: Optional[str] = None
    item_name: Optional[str] = None
    item_type: Optional[str] = None
    current_process_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PalletListResponse(BaseModel):
    items: List[PalletResponse]
    total: int
    page: int
    per_page: int
    pages: int


class PalletLinkLot(BaseModel):
    """LOT 연결 요청"""
    lot_id: int = Field(..., description="LOT ID")
    quantity: Optional[int] = Field(None, description="연결 수량 (미지정 시 LOT 전체 수량)")


class PalletForceStatusUpdate(BaseModel):
    """팔레트 상태 강제 변경 (실물 팔레트 status)"""
    status: str = Field(..., description="새 상태 (Hold, Stock, Empty 등)")
    reason: Optional[str] = Field(None, description="변경 사유")


class PalletStatusUpdate(BaseModel):
    """태그 상태 변경"""
    tag_status: str = Field(..., description="새 태그 상태 (AVAILABLE, IN_USE, DAMAGED)")
    reason: Optional[str] = Field(None, description="변경 사유")


class PalletTagStatusUpdate(BaseModel):
    """RFID 태그 상태 변경"""
    tag_status: str = Field(..., description="새 태그 상태 (AVAILABLE, IN_USE, DAMAGED)")
    reason: Optional[str] = Field(None, description="변경 사유")


class FIFOQueueItem(BaseModel):
    """FIFO 대기열 항목"""
    queue_position: int = Field(..., description="대기열 순서 (1부터 시작)")
    pallet_id: int
    pallet_no: str
    rfid_epc: str
    lot_no: Optional[str] = None
    item_code: Optional[str] = None
    item_name: Optional[str] = None
    created_at: datetime
    scan_status: str = Field(..., description="스캔 상태 (WAITING, OK, VIOLATION)")
    scan_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FIFOQueueResponse(BaseModel):
    """FIFO 대기열 응답"""
    items: List[FIFOQueueItem]
    total: int
