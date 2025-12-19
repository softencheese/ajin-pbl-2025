from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict

from app.core.database import get_db
from app.core.deps import get_admin_user
from app.models.user import User
from app.core.security import get_password_hash
from app.schemas.user import UserCreate, UserResponse

from app.core.config import settings

# 유저 관리는 기본적으로 Admin 권한 필요
# (세부 권한 관리도 Admin이 수행)
router = APIRouter(dependencies=[Depends(get_admin_user)])

@router.post("", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    사용자 생성 (Admin Only)
    
    기본적으로 USER 권한으로 생성되며, 추후 권한 수정 가능.
    새로운 USER는 config에 정의된 기본 읽기 권한을 자동으로 부여받음.
    """
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다")
        
    hashed_password = get_password_hash(user.password)
    
    # 기본 권한 설정 (USER 역할인 경우)
    default_permissions = {}
    if user.role == "USER":
        default_permissions = settings.DEFAULT_USER_PERMISSIONS
        
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        permissions=default_permissions
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """사용자 목록 조회"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 상세 조회"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user

@router.put("/{user_id}/permissions")
def update_user_permissions(
    user_id: int, 
    permissions: Dict[str, List[str]] = Body(..., example={"items": ["read", "write"]}), 
    db: Session = Depends(get_db)
):
    """
    사용자 세부 권한 수정 (Admin Only)
    
    예시 Body:
    {
        "items": ["read", "write"],
        "pallets": ["read"],
        "processes": []
    }
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
    # 기존 권한에 병합하거나 덮어쓰기 (여기서는 덮어쓰기)
    user.permissions = permissions
    db.commit()
    db.refresh(user)
    
    return {"message": "권한이 업데이트되었습니다", "username": user.username, "permissions": user.permissions}

@router.put("/{user_id}/role")
def update_user_role(
    user_id: int, 
    role: str = Body(..., embed=True), 
    db: Session = Depends(get_db)
):
    """사용자 역할 변경 (USER <-> ADMIN)"""
    if role not in ["USER", "ADMIN"]:
        raise HTTPException(status_code=400, detail="유효하지 않은 역할입니다")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
    user.role = role
    db.commit()
    db.refresh(user)
    
    return {"message": "역할이 업데이트되었습니다", "username": user.username, "role": user.role}
