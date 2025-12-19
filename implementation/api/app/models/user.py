from sqlalchemy import Column, String, Boolean, JSON, Integer, BigInteger
from app.models.base import BaseModel

class User(BaseModel):
    """사용자 관리 (Admin/User)"""
    __tablename__ = "users"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment='사용자 아이디')
    hashed_password = Column(String(255), nullable=False, comment='해싱된 비밀번호')
    full_name = Column(String(100), comment='사용자 실명')
    role = Column(String(20), default='USER', comment='권한 (ADMIN, USER)')
    is_active = Column(Boolean, default=True)
    
    # 세부 권한 (JSON)
    # 예: {"items": ["read", "write"], "pallets": ["read"]}
    permissions = Column(JSON, default=dict, comment='사용자 세부 권한 (JSON)')
