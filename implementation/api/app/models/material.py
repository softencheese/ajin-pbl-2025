from sqlalchemy import Column, Integer, String, Date, Boolean, BigInteger
from app.models.base import BaseModel

class RawMaterial(BaseModel):
    __tablename__ = "raw_materials"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    coil_number = Column(String(50), unique=True, nullable=False, comment='코일 번호 (C059461B) - 원자재 추적 키')
    material_name = Column(String(100), nullable=False, comment='원자재명')
    supplier = Column(String(100), comment='공급업체')
    receipt_date = Column(Date, comment='입고일자')
    qc_passed = Column(Boolean, default=False, comment='QC 합격 여부')
