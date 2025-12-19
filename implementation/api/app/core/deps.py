from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.user import TokenData

# OAuth2PasswordBearer는 Token URL을 가리킴 (auto_error=False로 설정하여 미제공 시 None 반환 허용)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    현재 로그인한 사용자 가져오기.
    AUTH_ENABLED가 False일 경우, 토큰 검증 없이 가짜 Admin 사용자를 반환합니다.
    """
    
    # 1. 인증 우회 모드 (AUTH_ENABLED = False)
    if not settings.AUTH_ENABLED:
        # 가짜 관리자 사용자 생성
        bypass_user = User(
            id=1, 
            username="admin_bypass", 
            role="ADMIN", 
            is_active=True,
            full_name="Bypass Admin"
        )
        return bypass_user
        
    # 2. 정상 모드인데 토큰이 없는 경우
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증되지 않았습니다 (토큰 없음)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. 정상 인증 모드
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="자격 증명을 검증할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """활성화된 사용자만 허용"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 사용자입니다")
    return current_user

async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """관리자 권한 확인"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="관리자 권한이 필요합니다"
        )
    return current_user
