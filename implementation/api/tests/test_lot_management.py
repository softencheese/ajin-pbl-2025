from fastapi.testclient import TestClient
from datetime import date
from app.models.item import Item
from app.models.process import Process
from app.models.lot import Lot
from sqlalchemy.orm import Session
import uuid

def test_create_production_lot(client: TestClient, db_session: Session):
    """생산 LOT 생성 테스트 (POST /lots)"""
    # 1. Get Master Data (WIP Item, Process, Worker)
    wip_item = db_session.query(Item).filter(Item.item_type == "WIP").first()
    process = db_session.query(Process).filter(Process.process_code == "PRESS").first()
    
    assert wip_item is not None
    assert process is not None
    
    # 2. Create Lot
    uid = str(uuid.uuid4())[:8]
    lot_no_suffix = f"PR-{uid}" # Avoid conflict
    
    payload = {
        "item_id": wip_item.id,
        "process_id": process.id,
        "quantity": 100,
        "production_date": date.today().isoformat(),
        "worker_name": "Test Worker",
        "barcode": f"BAR-{uid}" # Optional but good to test
    }
    
    response = client.post("/api/v1/lots", json=payload)
    if response.status_code != 201:
        print(f"Error: {response.json()}")
        
    assert response.status_code == 201
    data = response.json()
    assert data["item"]["id"] == wip_item.id
    assert data["quantity"] == 100
    # WIP 생산 LOT은 초기 상태 WAIT (다음 공정 대기)
    assert data["status"] in ("STOCK", "WAIT")

def test_update_lot_status(client: TestClient, db_session: Session):
    """LOT 상태 변경 테스트 (PUT /lots/{id}/status)"""
    db_session.rollback() # Ensure clean state
    # 1. Get existing Lot (from init_db)
    # Pick one generated lot
    lot = db_session.query(Lot).filter(Lot.status == "STOCK").first()
    assert lot is not None, "init_db should have created lots"
    
    # 2. Update Status
    payload = {
        "status": "HOLD",
        "notes": "Quality check"
    }
    
    response = client.put(f"/api/v1/lots/{lot.id}/status", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HOLD"
    
    # Verify DB
    # Re-query instead of refresh to avoid persistent state issues with TestClient
    updated_lot = db_session.query(Lot).filter(Lot.id == lot.id).first()
    assert updated_lot.status == "HOLD"
    assert updated_lot.notes == "Quality check"

def test_create_lot_genealogy_manual(client: TestClient, db_session: Session):
    """족보 수동 생성 테스트 (POST /lot-genealogy)"""
    # Need 2 lots: Input -> Output
    process = db_session.query(Process).first()
    
    # Create manual lots to avoid messing with existing complex genealogy
    uid = str(uuid.uuid4())[:8]
    item = db_session.query(Item).first()
    
    l1 = Lot(lot_number=f"G-IN-{uid}", item_id=item.id, quantity=100, initial_quantity=100, production_date=date.today())
    l2 = Lot(lot_number=f"G-OUT-{uid}", item_id=item.id, quantity=50, initial_quantity=50, production_date=date.today())
    db_session.add_all([l1, l2])
    db_session.commit()
    
    payload = {
        "input_lot_id": l1.id,
        "output_lot_id": l2.id,
        "process_id": process.id,
        "quantity_consumed": 10
    }
    
    response = client.post("/api/v1/lot-genealogy", json=payload)
    if response.status_code != 201:
        print(f"Genealogy Create Failed: {response.json()}")
    assert response.status_code == 201
    data = response.json()
    assert data["input_lot_id"] == l1.id
    assert data["output_lot_id"] == l2.id
    assert data["quantity_consumed"] == 10
