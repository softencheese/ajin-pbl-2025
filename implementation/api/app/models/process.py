from sqlalchemy import Column, Integer, String, BigInteger
from app.models.base import BaseModel

class Process(BaseModel):
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    process_code = Column(String(50), unique=True, nullable=False, comment='공정코드')
    process_name = Column(String(50), nullable=False, comment='공정명 (샤링, 프레스, 조립, 출하)')
    process_order = Column(Integer, nullable=False, comment='공정 순서')
    production_line = Column(String(50), comment='생산 라인 (400T, 1500T)')
