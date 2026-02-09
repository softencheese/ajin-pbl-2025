from fastapi.testclient import TestClient
from app.models.pallet import Pallet
from app.models.lot import Lot
from sqlalchemy.orm import Session
import uuid

def test_create_pallet(client: TestClient):
    """팔레트 생성 테스트 (POST /pallets)"""
    uid = str(uuid.uuid4())[:8]
    payload = {
        "pallet_no": f"PLT-{uid}",
        "rfid_epc": f"EPC-{uid}",
        "status": "Empty"
    }
    
    response = client.post("/api/v1/pallets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["pallet_no"] == f"PLT-{uid}"
    assert data["status"] == "Empty"
    assert data["rfid_epc"] == f"EPC-{uid}"

def test_link_lot_to_pallet(client: TestClient, db_session: Session):
    """팔레트에 LOT 연결 테스트 (PUT /pallets/{id}/link-lot)"""
    # 1. Create Data
    uid = str(uuid.uuid4())[:8]
    # Create PhysicalPallet + Pallet
    from app.models.physical_pallet import PhysicalPallet
    pp = PhysicalPallet(epc=f"EPC-L-{uid}", pallet_code=f"PLT-L-{uid}", status="Empty")
    db_session.add(pp)
    db_session.flush()
    p = Pallet(pallet_no=f"PLT-L-{uid}", physical_pallet_id=pp.id, status="Empty")
    db_session.add(p)
    
    # Create Lot (any item)
    from app.models.item import Item
    item = db_session.query(Item).first()
    l = Lot(lot_number=f"LOT-L-{uid}", item_id=item.id, quantity=100, initial_quantity=100, production_date="2024-01-01")
    db_session.add(l)
    db_session.commit()
    
    # 2. Link
    payload = {"lot_id": l.id}
    response = client.put(f"/api/v1/pallets/{p.id}/link-lot", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["lot_id"] == l.id
    # Usually linking lot changes status to Stock (if logic dictates) or remains Empty but has Lot?
    # Logic: If linking, it implies it's holding something. 
    # But API might not auto-change status unless explicit. 
    # Let's check logic: services/pallet_service.py usually updates status to Stock?
    # Assuming standard behavior, but verifying data linkage is key.

def test_force_status_change(client: TestClient, db_session: Session):
    """팔레트 상태 강제 변경 (PUT /pallets/{id}/status)"""
    p = db_session.query(Pallet).first()
    
    payload = {"status": "Hold", "reason": "Test Force"}
    response = client.put(f"/api/v1/pallets/{p.id}/status", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Hold"
    
def test_update_tag_status(client: TestClient, db_session: Session):
    """태그 상태 변경 (PUT /pallets/{id}/tag-status)"""
    p = db_session.query(Pallet).first()
    
    payload = {"tag_status": "DAMAGED", "reason": "Physical Damage"}
    response = client.put(f"/api/v1/pallets/{p.id}/tag-status", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["tag_status"] == "DAMAGED"
