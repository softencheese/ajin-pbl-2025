"""LOT 상세 조회 테스트 (GET /lots/{id})"""
from fastapi.testclient import TestClient
from datetime import date
from app.models.lot import Lot
from app.models.item import Item
from app.models.process import Process
from app.models.lot_genealogy import LotGenealogy
from sqlalchemy.orm import Session
import uuid


def test_get_lot_detail(client: TestClient, db_session: Session):
    """LOT 상세 조회 테스트 (GET /lots/{id})"""
    lot = db_session.query(Lot).first()
    assert lot is not None
    
    response = client.get(f"/api/v1/lots/{lot.id}")
    assert response.status_code == 200
    data = response.json()
    
    # 기본 필드 확인
    assert data["id"] == lot.id
    assert data["lot_number"] == lot.lot_number
    assert "quantity" in data
    assert "initial_quantity" in data
    assert "status" in data
    
    # 연관 데이터 확인 (item 정보 포함)
    if "item" in data and data["item"]:
        assert "id" in data["item"]
        assert "item_code" in data["item"]


def test_get_lot_detail_with_genealogy(client: TestClient, db_session: Session):
    """족보 정보가 있는 LOT 상세 조회"""
    uid = str(uuid.uuid4())[:8]
    
    item = db_session.query(Item).first()
    process = db_session.query(Process).first()
    
    # Parent LOT
    parent_lot = Lot(
        lot_number=f"PARENT-{uid}",
        item_id=item.id,
        quantity=100,
        initial_quantity=100,
        production_date=date.today(),
        status="STOCK"
    )
    db_session.add(parent_lot)
    db_session.commit()
    
    # Child LOT
    child_lot = Lot(
        lot_number=f"CHILD-{uid}",
        item_id=item.id,
        quantity=50,
        initial_quantity=50,
        production_date=date.today(),
        process_id=process.id,
        status="STOCK"
    )
    db_session.add(child_lot)
    db_session.commit()
    
    # Genealogy 연결
    genealogy = LotGenealogy(
        input_lot_id=parent_lot.id,
        output_lot_id=child_lot.id,
        process_id=process.id,
        quantity_consumed=30
    )
    db_session.add(genealogy)
    db_session.commit()
    
    # Child LOT 상세 조회
    response = client.get(f"/api/v1/lots/{child_lot.id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == child_lot.id
    assert data["process_id"] == process.id


def test_get_lot_not_found(client: TestClient):
    """존재하지 않는 LOT 상세 조회 - 404"""
    response = client.get("/api/v1/lots/999999")
    assert response.status_code == 404


def test_lot_list_pagination(client: TestClient):
    """LOT 목록 페이지네이션 테스트"""
    response = client.get("/api/v1/lots?page=1&per_page=10")
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert data["page"] == 1
    assert len(data["items"]) <= 10


def test_lot_list_filter_by_status(client: TestClient):
    """LOT 상태별 필터 테스트"""
    response = client.get("/api/v1/lots?status=STOCK")
    assert response.status_code == 200
    data = response.json()
    
    for lot in data["items"]:
        assert lot["status"] == "STOCK"


def test_lot_list_filter_by_item_type(client: TestClient):
    """품목 타입별 LOT 필터 테스트"""
    response = client.get("/api/v1/lots?item_type=RAW")
    assert response.status_code == 200
    data = response.json()
    
    # 결과가 있으면 item_type 확인
    if data["items"]:
        for lot in data["items"]:
            if "item" in lot and lot["item"]:
                assert lot["item"]["item_type"] == "RAW"


def test_lot_list_filter_by_date_range(client: TestClient, db_session: Session):
    """날짜 범위 필터 테스트"""
    today = date.today().isoformat()
    
    response = client.get(f"/api/v1/lots?date_from={today}&date_to={today}")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
