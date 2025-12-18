from sqlalchemy import Column, Integer, String, BigInteger, Boolean
from app.models.base import BaseModel

class Process(BaseModel):
    __tablename__ = "processes"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    process_code = Column(String(20), unique=True, nullable=False, comment='공정코드')
    process_name = Column(String(50), nullable=False, comment='공정명 (샤링, 프레스, 조립, 출하)')
    process_order = Column(Integer, nullable=False, comment='공정 순서')
    production_line = Column(String(50), comment='생산 라인 (400T, 1500T)')
    # 허용 아이템 타입 (쉼표로 구분, 예: "RAW,WIP")
    allowed_item_types = Column(String(100), comment='허용 아이템 타입 (RAW,WIP,PRODUCT)')
    # 첫 공정 여부 (샤링처럼 빈 팔레트에서 바로 생산 시작하는 공정)
    is_first_process = Column(Boolean, default=False, comment='첫 공정 여부 (빈 팔레트 → 바로 생산)')


