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
    # init_db creates pallets, so we expect some numbers
    assert data["active_pallets"] >= 0 
    assert "total_stock" in data
    assert data["total_stock"] >= 0
    assert "reader_status" in data
    assert data["reader_status"]["total"] >= 5 # We know init_db creates > 5 readers

def test_process_status(client: TestClient):
    response = client.get("/api/v1/dashboard/process-status")
    assert response.status_code == 200
    data = response.json()
    assert "processes" in data
    assert len(data["processes"]) >= 5 # init_db creates 5 processes
    
    # Check for specific process existence
    shear = next((p for p in data["processes"] if p["process_name"] == "샤링"), None)
    assert shear is not None
    assert "active_pallets" in shear

def test_reader_status(client: TestClient):
    response = client.get("/api/v1/dashboard/readers")
    assert response.status_code == 200
    data = response.json()
    assert "readers" in data
    assert len(data["readers"]) >= 5
    
    # Check for specific reader
    press_in = next((r for r in data["readers"] if "PRESS-IN" in r["port_name"]), None)
    assert press_in is not None

def test_inventory_stock(client: TestClient):
    response = client.get("/api/v1/dashboard/inventory/stock")
    assert response.status_code == 200
    data = response.json()
    assert "stock_items" in data
    # init_db creates LOTS, so we might have stock
    # If not, at least list should be valid
    assert isinstance(data["stock_items"], list)

def test_recent_activities(client: TestClient):
    """최근 활동 이력 조회 테스트"""
    response = client.get("/api/v1/dashboard/recent-activities")
    assert response.status_code == 200
    data = response.json()
    assert "activities" in data
    assert isinstance(data["activities"], list)
