from sqlalchemy import Column, String, Boolean, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

# RFIDTag 클래스 삭제됨 - pallets.tag_status로 통합


class RFIDReaderLocation(BaseModel):
    __tablename__ = "rfid_reader_locations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    port_name = Column(String(100), unique=True, nullable=False, comment='리더기 포트 식별자')
    process_id = Column(BigInteger, ForeignKey("processes.id"), nullable=True, comment='연결된 공정 ID')
    location_type = Column(String(20), nullable=True, comment='위치 유형 (IN, OUT, HOLD, DEFECT, FINISH)')
    description = Column(String(255), comment='설명')
    is_active = Column(Boolean, default=True, comment='활성 상태')
    last_scan_time = Column(DateTime, nullable=True, comment='마지막 스캔 시간')

    # Relationships
    process = relationship("Process")
