from sqlalchemy import Column, Integer, String, Date, Boolean, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Lot(BaseModel):
    __tablename__ = "lots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lot_no = Column(String(50), unique=True, nullable=False, comment='LOT 번호 (바코드)')
    part_id = Column(BigInteger, ForeignKey("parts.id"), nullable=False, comment='품번 ID')
    process_id = Column(BigInteger, ForeignKey("processes.id"), nullable=False, comment='공정 ID')
    material_id = Column(BigInteger, ForeignKey("raw_materials.id"), comment='원자재 ID (원자재 추적용)')
    assembly_level = Column(Integer, default=0, comment='조립 레벨 (중간품은 항상 0)')
    quantity = Column(Integer, nullable=False, comment='수량 (400 EA, 40 EA)')
    production_date = Column(Date, nullable=False, comment='생산일자 (25-04-26, 25-10-17)')
    worker_name = Column(String(50), comment='작업자 (최영일, 전재민)')
    qc_passed = Column(Boolean, default=False, comment='QC 합격 여부')

    # Relationships
    part = relationship("Part")
    process = relationship("Process")
    material = relationship("RawMaterial")
