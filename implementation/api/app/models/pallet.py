from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Pallet(BaseModel):
    __tablename__ = "pallets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pallet_no = Column(String(50), unique=True, nullable=False, comment='팔레트 번호')
    rfid_epc = Column(String(100), unique=True, comment='RFID EPC 코드')
    lot_id = Column(BigInteger, ForeignKey("lots.id"), comment='연결된 중간품 LOT ID')
    assembly_lot_id = Column(BigInteger, ForeignKey("assembly_lots.id"), comment='연결된 조립품 LOT ID')
    status = Column(String(20), default='Generated', comment='상태 (Generated, Empty, Stock, Consuming, Producing, Finished, Deregistered, Hold, Defect)')
    current_process_id = Column(BigInteger, ForeignKey("processes.id"), comment='현재 공정')
    quantity = Column(Integer, default=0, comment='현재 적재 수량')

    # Relationships
    lot = relationship("Lot")
    assembly_lot = relationship("AssemblyLot")
    current_process = relationship("Process")
    histories = relationship("PalletHistory", back_populates="pallet")


class PalletHistory(BaseModel):
    __tablename__ = "pallet_histories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pallet_id = Column(BigInteger, ForeignKey("pallets.id"), nullable=False, comment='팔레트 ID')
    lot_id = Column(BigInteger, ForeignKey("lots.id"), comment='중간품 LOT ID')
    assembly_lot_id = Column(BigInteger, ForeignKey("assembly_lots.id"), comment='조립품 LOT ID')
    process_id = Column(BigInteger, ForeignKey("processes.id"), comment='공정 ID')
    location_type = Column(String(20), comment='위치 유형 (IN, OUT, HOLD, DEFECT, FINISH)')
    previous_status = Column(String(20), comment='이전 상태')
    current_status = Column(String(20), nullable=False, comment='현재 상태')
    event_type = Column(String(50), nullable=False, comment='이벤트 유형 (TAG_SCAN, STATUS_CHANGE)')
    event_time = Column(DateTime, comment='이벤트 발생 시간')
    worker_name = Column(String(50), comment='작업자')

    # Relationships
    pallet = relationship("Pallet", back_populates="histories")
    lot = relationship("Lot")
    assembly_lot = relationship("AssemblyLot")
    process = relationship("Process")
