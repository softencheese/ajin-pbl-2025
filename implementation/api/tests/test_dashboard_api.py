from fastapi.testclient import TestClient
from app.models.pallet import Pallet
from app.models.process import Process
from app.models.item import Item
from app.models.rfid import RFIDReaderLocation
from datetime import date

def test_dashboard_summary(client: TestClient):
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "active_pallets" in data
    assert "total_stock" in data
    assert "today_production" in data
    assert "reader_status" in data

def test_process_status(client: TestClient):
    # Ensure at least one process exists
    client.post("/api/v1/processes/", json={
        "process_code": "P1", "process_name": "Proc1", "process_order": 1
    })
    
    response = client.get("/api/v1/dashboard/process-status")
    assert response.status_code == 200
    data = response.json()
    assert "processes" in data
    assert isinstance(data["processes"], list)

def test_reader_status(client: TestClient):
    response = client.get("/api/v1/dashboard/readers")
    assert response.status_code == 200
    data = response.json()
    assert "readers" in data
    assert isinstance(data["readers"], list)

def test_inventory_stock(client: TestClient):
    response = client.get("/api/v1/dashboard/inventory/stock")
    assert response.status_code == 200
    data = response.json()
    assert "stock_items" in data


def test_recent_activities(client: TestClient):
    """최근 활동 이력 조회 테스트"""
    response = client.get("/api/v1/dashboard/recent-activities")
    assert response.status_code == 200
    data = response.json()
    assert "activities" in data
    assert "total" in data
    assert isinstance(data["activities"], list)
