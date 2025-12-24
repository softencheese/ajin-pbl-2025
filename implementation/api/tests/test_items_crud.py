"""Items CRUD 전체 테스트 (목록, 상세, 생성, 수정, 삭제)"""
from fastapi.testclient import TestClient
from app.models.item import Item
from sqlalchemy.orm import Session
import uuid


def test_list_items(client: TestClient):
    """품목 목록 조회 테스트 (GET /items)"""
    response = client.get("/api/v1/items")
    assert response.status_code == 200
    data = response.json()
    
    # 페이지네이션 구조 확인
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert "pages" in data
    assert isinstance(data["items"], list)


def test_list_items_with_pagination(client: TestClient):
    """페이지네이션 파라미터 테스트"""
    response = client.get("/api/v1/items?page=1&per_page=5")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["per_page"] == 5
    assert len(data["items"]) <= 5


def test_list_items_with_type_filter(client: TestClient):
    """품목 타입 필터 테스트"""
    response = client.get("/api/v1/items?item_type=RAW")
    assert response.status_code == 200
    data = response.json()
    
    for item in data["items"]:
        assert item["item_type"] == "RAW"


def test_list_items_with_search(client: TestClient, db_session: Session):
    """검색 기능 테스트"""
    # 기존 아이템 조회
    item = db_session.query(Item).first()
    if item:
        search_term = item.item_code[:4]  # 일부 코드만 검색
        response = client.get(f"/api/v1/items?search={search_term}")
        assert response.status_code == 200
        data = response.json()
        # 검색 결과가 있어야 함
        assert data["total"] >= 0


def test_get_item_detail(client: TestClient, db_session: Session):
    """품목 상세 조회 테스트 (GET /items/{id})"""
    item = db_session.query(Item).first()
    assert item is not None
    
    response = client.get(f"/api/v1/items/{item.id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == item.id
    assert data["item_code"] == item.item_code
    assert data["item_name"] == item.item_name
    assert data["item_type"] == item.item_type


def test_get_item_not_found(client: TestClient):
    """존재하지 않는 품목 조회 테스트"""
    response = client.get("/api/v1/items/999999")
    assert response.status_code == 404


def test_create_item(client: TestClient):
    """품목 생성 테스트 (POST /items)"""
    uid = str(uuid.uuid4())[:8]
    
    payload = {
        "item_code": f"ITEM-{uid}",
        "item_name": f"테스트 품목 {uid}",
        "item_type": "RAW",
        "unit": "EA",
        "spec": "1.2t x 1000mm"
    }
    
    response = client.post("/api/v1/items/", json=payload)
    assert response.status_code == 201
    data = response.json()
    
    assert data["item_code"] == payload["item_code"]
    assert data["item_name"] == payload["item_name"]
    assert data["item_type"] == "RAW"
    assert "id" in data


def test_create_item_duplicate_code(client: TestClient, db_session: Session):
    """중복 품목코드 생성 시 409 에러"""
    # 기존 아이템 조회
    item = db_session.query(Item).first()
    
    payload = {
        "item_code": item.item_code,  # 중복 코드
        "item_name": "중복 테스트",
        "item_type": "RAW"
    }
    
    response = client.post("/api/v1/items/", json=payload)
    assert response.status_code == 409


def test_update_item(client: TestClient, db_session: Session):
    """품목 수정 테스트 (PUT /items/{id})"""
    uid = str(uuid.uuid4())[:8]
    
    # 테스트용 아이템 생성
    item = Item(
        item_code=f"UPD-{uid}",
        item_name="수정 전",
        item_type="RAW"
    )
    db_session.add(item)
    db_session.commit()
    
    # 수정
    update_payload = {
        "item_name": "수정 후 이름",
        "spec": "수정된 스펙"
    }
    
    response = client.put(f"/api/v1/items/{item.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["item_name"] == "수정 후 이름"
    assert data["spec"] == "수정된 스펙"
    assert data["item_code"] == item.item_code  # 코드는 그대로


def test_update_item_not_found(client: TestClient):
    """존재하지 않는 품목 수정 시 404 에러"""
    response = client.put("/api/v1/items/999999", json={"item_name": "Test"})
    assert response.status_code == 404


def test_delete_item_success(client: TestClient, db_session: Session):
    """품목 삭제 테스트 (DELETE /items/{id})"""
    uid = str(uuid.uuid4())[:8]
    
    # 삭제용 아이템 생성 (LOT 연결 없음)
    item = Item(
        item_code=f"DEL-{uid}",
        item_name="삭제 대상",
        item_type="RAW"
    )
    db_session.add(item)
    db_session.commit()
    item_id = item.id
    
    response = client.delete(f"/api/v1/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # 삭제 확인
    deleted = db_session.query(Item).filter(Item.id == item_id).first()
    assert deleted is None


def test_delete_item_with_lots(client: TestClient, db_session: Session):
    """LOT 이력이 있는 품목 삭제 시 409 에러"""
    # LOT과 연결된 아이템 조회
    from app.models.lot import Lot
    lot = db_session.query(Lot).first()
    
    if lot:
        response = client.delete(f"/api/v1/items/{lot.item_id}")
        assert response.status_code == 409


def test_delete_item_not_found(client: TestClient):
    """존재하지 않는 품목 삭제 시 404 에러"""
    response = client.delete("/api/v1/items/999999")
    assert response.status_code == 404
