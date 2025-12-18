from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Pallet(BaseModel):
    """팔레트 + RFID 태그 통합 관리 (기존 rfid_tags 테이블 흡수)"""
    __tablename__ = "pallets"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    pallet_no = Column(String(50), unique=True, nullable=False, comment='팔레트 번호')
    rfid_epc = Column(String(100), unique=True, comment='RFID EPC 코드')
    lot_id = Column(BigInteger, ForeignKey("lots.id"), comment='연결된 LOT ID')
    status = Column(String(20), default='Generated', comment='상태 (Generated, Empty, Stock, Consuming, Producing, Finished, Deregistered, Hold, Defect)')
    tag_status = Column(String(20), default='AVAILABLE', comment='RFID 태그 상태 (AVAILABLE, IN_USE, DAMAGED)')
    current_process_id = Column(BigInteger, ForeignKey("processes.id"), comment='현재 공정')
    quantity = Column(Integer, default=0, comment='현재 적재 수량')
    tag_registered_at = Column(DateTime, comment='RFID 태그 등록 시각')
    tag_deregistered_at = Column(DateTime, comment='RFID 태그 해제 시각')

    # Relationships
    lot = relationship("Lot")
    current_process = relationship("Process")
    histories = relationship("PalletHistory", back_populates="pallet")


class PalletHistory(BaseModel):
    """팔레트 상태 변경 이력 (불변 로그)"""
    __tablename__ = "pallet_histories"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    pallet_id = Column(BigInteger, ForeignKey("pallets.id"), nullable=False, comment='팔레트 ID')
    lot_id = Column(BigInteger, ForeignKey("lots.id"), comment='LOT ID')
    process_id = Column(BigInteger, ForeignKey("processes.id"), comment='공정 ID')
    reader_location_id = Column(BigInteger, ForeignKey("rfid_reader_locations.id"), nullable=True, comment='리더기 위치 ID')
    location_type = Column(String(20), comment='위치 유형 (IN, OUT, HOLD, DEFECT, FINISH, RETURN)')
    previous_status = Column(String(20), comment='이전 상태')
    new_status = Column(String(20), nullable=False, comment='새 상태')
    event_type = Column(String(50), nullable=False, comment='이벤트 유형 (SCAN, STATUS_CHANGE, FIFO_VIOLATION 등)')
    scan_time = Column(DateTime, comment='스캔 시각')
    worker_name = Column(String(50), comment='작업자')
    notes = Column(Text, comment='비고 (FIFO 위반 등)')

    # Relationships
    pallet = relationship("Pallet", back_populates="histories")
    lot = relationship("Lot")
    process = relationship("Process")
