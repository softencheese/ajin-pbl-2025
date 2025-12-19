from typing import List
from fastapi import Depends, HTTPException
from app.core.deps import get_current_active_user
from app.models.user import User
from app.core.config import settings

class PermissionChecker:
    """
    세부 권한(Granular Permission) 체크
    
    사용 예:
    Depends(PermissionChecker("items", "read"))
    Depends(PermissionChecker("pallets", "write"))
    """
    def __init__(self, resource: str, action: str):
        self.resource = resource # items, pallets, processes, users, ...
        self.action = action     # read, write
    
    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        # 1. Bypass 모드인 경우 통과 (단, settings.AUTH_ENABLED 체크는 get_current_user에서 이미 수행됨)
        # 하지만 명시적으로 여기서도 체크 가능
        if not settings.AUTH_ENABLED:
            return user
            
        # 2. 슈퍼 관리자(ROLE=ADMIN)는 모든 권한 가짐
        if user.role == "ADMIN":
            return user
            
        # 3. 권한 체크
        # user.permissions = {"items": ["read"], "pallets": ["read", "write"]}
        user_perms = user.permissions or {}
        resource_perms = user_perms.get(self.resource, [])
        
        if self.action not in resource_perms:
            raise HTTPException(
                status_code=403, 
                detail=f"권한이 부족합니다. ({self.resource}에 대한 {self.action} 권한 필요)"
            )
            
        return user
