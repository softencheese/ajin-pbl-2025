from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, List

class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    role: str = "USER"
    is_active: bool = True
    permissions: Optional[Dict[str, List[str]]] = {}

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str
