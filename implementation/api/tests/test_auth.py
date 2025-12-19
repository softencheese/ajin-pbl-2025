
import pytest
from unittest.mock import patch
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.user import User
from app.core.deps import get_current_user
from main import app


import pytest
from unittest.mock import patch
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.user import User
from app.core.deps import get_current_user
from main import app

# 실제 라우터를 테스트하므로 더미 라우터 제거

def test_auth_bypass_mode(client: TestClient):
    """
    AUTH_ENABLED = False (전제: dev 모드)
    토큰 없이 보호된 API(Dashboard) 접근 시 200 OK
    """
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    # Bypass Admin으로 처리되었는지 확인은 Response Body로 알 수 없지만,
    # 200 OK가 떨어졌다는 것 자체가 인증 통과 의미
    
def test_create_user_and_login(client: TestClient, db_session: Session):
    """
    사용자 생성 후 로그인 및 토큰 발급 테스트
    """
    password = "testpassword"
    user = User(
        username="testuser",
        hashed_password=get_password_hash(password),
        full_name="Test User",
        role="USER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_login_wrong_password(client: TestClient, db_session: Session):
    password = "testpassword"
    user = User(
        username="wronguser",
        hashed_password=get_password_hash(password),
        role="USER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "wronguser", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401

@patch("app.core.config.settings.AUTH_ENABLED", True)
def test_protected_route_with_token(client: TestClient, db_session: Session):
    """
    AUTH_ENABLED = True 시, User 토큰으로 Dashboard(User Level) 접근 성공
    """
    password = "realpassword"
    user = User(
        username="realuser",
        hashed_password=get_password_hash(password),
        role="USER",
        is_active=True,
        permissions={"dashboard": ["read"]}
    )
    db_session.add(user)
    db_session.commit()
    
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "realuser", "password": password}
    )
    token = login_res.json()["access_token"]
    
    response = client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

@patch("app.core.config.settings.AUTH_ENABLED", True)
def test_admin_route_forbidden_for_user(client: TestClient, db_session: Session):
    """
    AUTH_ENABLED = True 시, User 토큰으로 Items(Admin Level) 접근 시 403 Forbidden 확인
    """
    password = "realuserpass"
    user = User(
        username="normuser",
        hashed_password=get_password_hash(password),
        role="USER", # 일반 유저
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "normuser", "password": password}
    )
    token = login_res.json()["access_token"]
    
    # Items API는 Admin Only
    response = client.get(
        "/api/v1/items",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403 # Forbidden

@patch("app.core.config.settings.AUTH_ENABLED", True)
def test_protected_route_no_token(client: TestClient):
    """
    AUTH_ENABLED = True 상태에서 토큰 없이 접근 시 401 에러
    """
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 401


