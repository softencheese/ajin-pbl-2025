"""실물 팔레트 모델"""
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class PalletStatus(str, enum.Enum):
    """팔레트 상태 ENUM"""
    GENERATED = 'Generated'
    EMPTY = 'Empty'
    STOCK = 'Stock'
    CONSUMING = 'Consuming'
    PRODUCING = 'Producing'
    FINISHED = 'Finished'
    DEREGISTERED = 'Deregistered'
    HOLD = 'Hold'
    DEFECT = 'Defect'


class PhysicalPallet(BaseModel):
    """실물 팔레트 정보"""
    __tablename__ = "physical_pallets"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    # API에서는 epc로 사용하지만 DB 컬럼명은 rfid_epc
    epc = Column('rfid_epc', String(100), unique=True, nullable=False, comment='RFID EPC 코드')
    pallet_code = Column(String(50), unique=True, nullable=False, comment='팔레트 실물 코드')
    item_id = Column(BigInteger, ForeignKey("items.id"), comment='기본 적재 품목 ID')
    status = Column(Enum(PalletStatus, values_callable=lambda x: [e.value for e in x]), default=PalletStatus.GENERATED, comment='팔레트 상태')
    description = Column(String(200), comment='팔레트 설명')

    # Relationships
    item = relationship("Item", foreign_keys=[item_id])
