from sqlalchemy import Column, String, Boolean, Integer, BigInteger
from app.models.base import BaseModel


class Item(BaseModel):
    """통합 품목 마스터 (원자재, 재공품, 완제품)"""
    __tablename__ = "items"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    item_code = Column(String(50), unique=True, nullable=False, comment='품번 또는 원자재코드 (고유)')
    item_name = Column(String(200), nullable=False, comment='품명')
    item_type = Column(String(20), nullable=False, comment='품목 유형 (RAW, WIP, PRODUCT)')
    unit = Column(String(20), default='EA', comment='단위')
    spec = Column(String(200), comment='규격 (LH/RH, 색상, 재질 등)')
    vehicle_model = Column(String(50), comment='적용 차종 (JX1, NE)')
    default_supplier = Column(String(100), comment='기본 공급사 (원자재인 경우)')
    is_active = Column(Boolean, default=True, comment='사용 여부')
    pallet_capacity = Column(Integer, default=10, comment='권장 팔레트 적재 용량')
