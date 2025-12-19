
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.user import User
from main import app

# AUTH_ENABLED=True 강제 적용
@patch("app.core.config.settings.AUTH_ENABLED", True)
def test_granular_read_permission(client: TestClient, db_session: Session):
    """
    items:read 권한만 가진 사용자는 조회 성공, 생성 실패 확인
    """
    password = "readuserpass"
    user = User(
        username="itemreader",
        hashed_password=get_password_hash(password),
        full_name="Item Reader",
        role="USER",
        is_active=True,
        permissions={"items": ["read"]}
    )
    db_session.add(user)
    db_session.commit()
    
    # 로그인
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "itemreader", "password": password}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. GET /items (read 권한 있음) -> 200 OK
    res_get = client.get("/api/v1/items", headers=headers)
    assert res_get.status_code == 200
    
    # 2. POST /items (write 권한 없음) -> 403 Forbidden
    res_post = client.post(
        "/api/v1/items", 
        headers=headers,
        json={
            "item_code": "TEST-ITEM-01",
            "item_name": "Test Item",
            "item_type": "RAW"
        }
    )
    assert res_post.status_code == 403

@patch("app.core.config.settings.AUTH_ENABLED", True)
def test_granular_write_permission(client: TestClient, db_session: Session):
    """
    items:write 권한을 가진 사용자는 생성 성공 확인
    """
    password = "writeuserpass"
    user = User(
        username="itemwriter",
        hashed_password=get_password_hash(password),
        full_name="Item Writer",
        role="USER",
        is_active=True,
        permissions={"items": ["write"]}
    )
    db_session.add(user)
    db_session.commit()
    
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "itemwriter", "password": password}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # POST /items -> 201 Created
    res_post = client.post(
        "/api/v1/items", 
        headers=headers,
        json={
            "item_code": "TEST-ITEM-02",
            "item_name": "Test Item 2",
            "item_type": "RAW"
        }
    )
    assert res_post.status_code == 201

@patch("app.core.config.settings.AUTH_ENABLED", True)
def test_no_permission(client: TestClient, db_session: Session):
    """
    권한 없는 사용자는 접근 거부 (403) 확인
    """
    password = "nopermpass"
    # 명시적으로 permissions를 빈 dict로 설정하여 기본 권한 부여 우회
    user = User(
        username="nopermuser",
        hashed_password=get_password_hash(password),
        role="USER",
        is_active=True,
        permissions={} # 권한 없음
    )
    db_session.add(user)
    db_session.commit()
    
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "nopermuser", "password": password}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # GET /items -> 403 Forbidden
    res = client.get("/api/v1/items", headers=headers)
    assert res.status_code == 403

@patch("app.core.config.settings.AUTH_ENABLED", True)
def test_admin_override(client: TestClient, db_session: Session):
    """
    관리자(ADMIN)는 권한 설정 없어도 모든 접근 가능 확인
    """
    password = "adminpass"
    user = User(
        username="superadmin",
        hashed_password=get_password_hash(password),
        role="ADMIN",
        is_active=True,
        permissions={} # 권한 비어있음
    )
    db_session.add(user)
    db_session.commit()
    
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "superadmin", "password": password}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # GET /items -> 200 OK
    res_get = client.get("/api/v1/items", headers=headers)
    assert res_get.status_code == 200
    
    # POST /items -> 201 (or 409 if duplicate)
    res_post = client.post(
        "/api/v1/items", 
        headers=headers,
        json={
            "item_code": "ADMIN-ITEM",
            "item_name": "Admin Item",
            "item_type": "PRODUCT"
        }
    )
    assert res_post.status_code == 201

@patch("app.core.config.settings.AUTH_ENABLED", True)
def test_update_permissions(client: TestClient, db_session: Session):
    """
    관리자가 유저의 권한을 업데이트하고 반영되는지 테스트
    """
    # 관리자 생성
    admin_user = User(
        username="permissionadmin",
        hashed_password=get_password_hash("admin"),
        role="ADMIN",
        is_active=True
    )
    db_session.add(admin_user)
    
    # 대상 유저 생성 (처음엔 빈 권한으로 생성)
    target_user = User(
        username="targetuser",
        hashed_password=get_password_hash("user"),
        role="USER",
        is_active=True,
        permissions={} 
    )
    db_session.add(target_user)
    db_session.commit()
    
    # 관리자 로그인
    login_res = client.post("/api/v1/auth/login", data={"username": "permissionadmin", "password": "admin"})
    admin_token = login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 대상 유저 로그인
    target_login = client.post("/api/v1/auth/login", data={"username": "targetuser", "password": "user"})
    target_token = target_login.json()["access_token"]
    target_headers = {"Authorization": f"Bearer {target_token}"}
    
    # 1. 대상 유저: GET /items -> 403 (권한 없음)
    assert client.get("/api/v1/items", headers=target_headers).status_code == 403
    
    # 2. 관리자가 권한 부여 (PUT /users/{id}/permissions)
    perms_data = {"items": ["read"]}
    res_put = client.put(
        f"/api/v1/users/{target_user.id}/permissions",
        headers=admin_headers,
        json=perms_data
    )
    assert res_put.status_code == 200
    assert res_put.json()["permissions"] == perms_data
    
    # 3. 대상 유저: GET /items -> 200 (권한 획득)
    assert client.get("/api/v1/items", headers=target_headers).status_code == 200

@patch("app.core.config.settings.AUTH_ENABLED", True)
def test_default_permissions_on_create(client: TestClient, db_session: Session):
    """
    새로운 유저 생성 시 기본 읽기 권한이 자동으로 부여되는지 확인
    """
    # 관리자 생성
    admin_user = User(
        username="creatoradmin",
        hashed_password=get_password_hash("admin"),
        role="ADMIN",
        is_active=True
    )
    db_session.add(admin_user)
    db_session.commit()
    
    # 관리자 로그인
    login_res = client.post("/api/v1/auth/login", data={"username": "creatoradmin", "password": "admin"})
    admin_token = login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 새로운 유저 생성 API 호출
    new_user_data = {
        "username": "newemployee",
        "password": "password123",
        "full_name": "New Employee",
        "role": "USER"
    }
    res_create = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json=new_user_data
    )
    assert res_create.status_code == 201
    created_user = res_create.json()
    
    
    # 기본 권한 확인 (Master Data: Read Only / Operational Data: Read & Write)
    perms = created_user["permissions"]
    
    # 1. Master Data (Items) - Read Only
    assert "items" in perms
    assert "read" in perms["items"]
    assert "write" not in perms["items"]
    
    # 2. Operational Data (Lots) - Read & Write
    assert "lots" in perms
    assert "read" in perms["lots"]
    assert "write" in perms["lots"]

    # 3. Operational Data (Pallets) - Read & Write
    assert "pallets" in perms
    assert "write" in perms["pallets"]
    
    # 해당 유저로 로그인하여 실제 접근 테스트
    user_login = client.post("/api/v1/auth/login", data={"username": "newemployee", "password": "password123"})
    user_token = user_login.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    
    # 4. Master Data (Items) 접근 테스트
    # GET /items -> 200 OK (기본 읽기 권한)
    assert client.get("/api/v1/items", headers=user_headers).status_code == 200
    # POST /items -> 403 Forbidden (쓰기 권한 없음)
    res_post_item = client.post(
        "/api/v1/items", 
        headers=user_headers,
        json={"item_code": "FAIL", "item_name": "Fail", "item_type": "RAW"}
    )
    assert res_post_item.status_code == 403

    # 5. Operational Data (Lots) 접근 테스트
    # POST /lots -> 201 Created (쓰기 권한 있음)
    # (참고: 로트 생성은 Items 등 FK 제약이 있을 수 있으나, 권한 체크는 진입 시점에 이루어짐. 
    #  여기서는 유효한 데이터로 시도 또는 403이 아닌 다른 에러(400/404/422/201)가 나오면 권한 통과로 간주)
    #  안전하게 201을 기대하려면 유효한 ItemCode가 필요함.
    #  테스트 편의상 권한 체크 통과 여부는 "403이 아님"으로도 1차 검증 가능하나, 
    #  더 확실히 하기 위해 write permission check 통과 후 비즈니스 로직 에러가 나는지 확인.
    
    # 빈 데이터로 호출하면 Validation Error(422) 발생 -> 즉 권한 체크(403)은 통과함
    res_post_lot = client.post("/api/v1/lots/receiving", headers=user_headers, json={})
    assert res_post_lot.status_code != 403
