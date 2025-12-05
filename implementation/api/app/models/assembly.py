from sqlalchemy import Column, Integer, String, Date, Boolean, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class AssemblyLot(BaseModel):
    __tablename__ = "assembly_lots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lot_no = Column(String(50), unique=True, nullable=False, comment='조립품 LOT 번호 (ASM-XXX)')
    part_id = Column(BigInteger, ForeignKey("parts.id"), nullable=False, comment='조립품 품번')
    assembly_level = Column(Integer, default=0, comment='조립 단계')
    assembly_date = Column(Date, nullable=False, comment='조립 완료일')
    quantity = Column(Integer, nullable=False, comment='조립 수량')
    worker_name = Column(String(50), comment='작업자')
    qc_passed = Column(Boolean, default=False, comment='QC 합격 여부')

    # Relationships
    part = relationship("Part")
    components = relationship("AssemblyComponent", foreign_keys="[AssemblyComponent.assembly_lot_id]", back_populates="assembly_lot")

class AssemblyComponent(BaseModel):
    __tablename__ = "assembly_components"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    assembly_lot_id = Column(BigInteger, ForeignKey("assembly_lots.id"), nullable=False, comment='조립품 LOT ID')
    component_lot_id = Column(BigInteger, ForeignKey("lots.id"), comment='투입된 중간품 LOT ID')
    component_assembly_id = Column(BigInteger, ForeignKey("assembly_lots.id"), comment='투입된 하위 조립품 LOT ID')
    component_pallet_id = Column(BigInteger, ForeignKey("pallets.id"), comment='투입 팔레트')
    required_quantity_per_unit = Column(Integer, nullable=False, comment='조립품 1개당 필요한 구성품 수량')
    total_consumed_quantity = Column(Integer, nullable=False, comment='실제 총 소비 수량')

    # Relationships
    assembly_lot = relationship("AssemblyLot", foreign_keys=[assembly_lot_id], back_populates="components")
    component_lot = relationship("Lot")
    component_assembly = relationship("AssemblyLot", foreign_keys=[component_assembly_id])
    # component_pallet relationship will be defined in pallet.py or using string reference here if needed, 
    # but since Pallet is not yet defined, we'll use string reference.
    component_pallet = relationship("Pallet", foreign_keys=[component_pallet_id])
