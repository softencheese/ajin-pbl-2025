from sqlalchemy import Column, Integer, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class LotGenealogy(BaseModel):
    """LOT 족보 (투입-산출 관계, 추적성 핵심)"""
    __tablename__ = "lot_genealogy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    input_lot_id = Column(BigInteger, ForeignKey("lots.id"), nullable=False, index=True, comment='투입 LOT ID (부모)')
    output_lot_id = Column(BigInteger, ForeignKey("lots.id"), nullable=False, index=True, comment='생성 LOT ID (자식)')
    process_id = Column(BigInteger, ForeignKey("processes.id"), nullable=False, index=True, comment='발생 공정 ID')
    quantity_consumed = Column(Integer, nullable=False, comment='투입 수량')

    # Relationships
    input_lot = relationship("Lot", foreign_keys=[input_lot_id], backref="children_genealogy")
    output_lot = relationship("Lot", foreign_keys=[output_lot_id], backref="parent_genealogy")
    process = relationship("Process")
