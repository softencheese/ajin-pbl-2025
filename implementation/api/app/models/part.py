from sqlalchemy import Column, Integer, String, Boolean, BigInteger
from app.models.base import BaseModel

class Part(BaseModel):
    __tablename__ = "parts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    part_number = Column(String(50), unique=True, nullable=False, comment='품번 (71412-T6000S, 76211-GI000)')
    part_name = Column(String(100), nullable=False, comment='품명 (PNL-FR DR INR, LH)')
    part_spec = Column(String(200), comment='부품 사양/메모 (LH/RH, 색상, 위치, 재질 등)')
    vehicle_model = Column(String(50), comment='차종 (JX1, NE)')
    is_assembly = Column(Boolean, default=False, comment='조립품 여부 (TRUE: 조립품, FALSE: 중간품)')
    is_final_product = Column(Boolean, default=False, comment='최종 완제품 여부')
