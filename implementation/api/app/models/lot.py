from sqlalchemy import Column, Integer, String, Date, Boolean, BigInteger, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Lot(BaseModel):
    """통합 LOT 관리 (원자재, 중간품, 완제품 모두 포함)"""
    __tablename__ = "lots"

    id = Column(Integer, primary_key=True, index=True)
    lot_number = Column(String(50), unique=True, index=True, nullable=False, comment="LOT 번호")
    barcode = Column(String(100), comment="실물 바코드 번호 (라벨 스캔용)")
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True, comment='품목 ID')
    quantity = Column(Integer, nullable=False, comment='현재 수량')
    initial_quantity = Column(Integer, nullable=False, comment='초기 수량')
    status = Column(String(20), default='WAIT', comment='LOT 상태 (WAIT, PROCESS, STOCK, CONSUMED, SHIPPED, HOLD, DEFECT)')
    production_date = Column(Date, nullable=False, comment='생산일 또는 입고일')
    process_id = Column(Integer, ForeignKey("processes.id"), comment='생성된 공정 ID')
    supplier = Column(String(100), comment='공급사 (원자재 입고 시, 기본 공급사와 다를 경우)')
    worker_name = Column(String(50), comment='작업자')
    qc_passed = Column(Boolean, default=False, comment='QC 합격 여부')
    notes = Column(Text, comment='비고')

    # Relationships
    item = relationship("Item")
    process = relationship("Process")
