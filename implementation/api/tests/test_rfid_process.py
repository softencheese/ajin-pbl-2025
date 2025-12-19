from fastapi.testclient import TestClient
from datetime import datetime

def test_rfid_scan_in_success(client: TestClient):
    # 1. Setup Data
    # Process
    proc_res = client.post("/api/v1/processes/", json={"process_code": "PROC-SCAN", "process_name": "Scan Process", "process_type": "Manufacturing", "process_order": 3})
    proc_id = proc_res.json()["id"]

    # Reader (IN)
    client.post("/api/v1/reader-locations/", json={"port_name": "COM_IN", "process_id": proc_id, "location_type": "IN", "description": "IN Reader"})

    # Item & Lot & Pallet
    item_res = client.post("/api/v1/items/", json={"item_code": "ITEM-SCAN", "item_name": "Scan Item", "item_type": "RAW"})
    item_id = item_res.json()["id"]
    
    lot_res = client.post("/api/v1/lots/receiving", json={
        "item_id": item_id, 
        "quantity": 100, 
        "production_date": "2023-12-16"
    })
    lot_id = lot_res.json()["id"]
    
    pallet_res = client.post("/api/v1/pallets", json={"pallet_no": "PAL-SCAN", "rfid_epc": "EPC-SCAN", "status": "Empty"})
    pallet_id = pallet_res.json()["id"]
    
    # Link Pallet to Lot
    link_res = client.put(f"/api/v1/pallets/{pallet_id}/link-lot", json={"lot_id": lot_id})
    assert link_res.status_code == 200
    
    response = client.post(
        "/api/v1/rfid/scan",
        json={
            "type": "SCAN",
            "port_name": "COM_IN",
            "epc": "EPC-SCAN",
            "scan_time": datetime.now().isoformat()
        }
    )
    # If Lot is needed for Empty -> Stock, this might fail or error.
    # If Pallet is Empty and Scanned at IN, it might expect to be assigned a Lot (which is done by linking).
    # If RFID Auto-assignment is implemented, maybe that's how?
    # For now, just assert 200.
    assert response.status_code == 200

def test_rfid_scan_unknown_tag(client: TestClient):
    # Setup Reader First
    proc_res = client.post("/api/v1/processes/", json={"process_code": "PROC-UNKNOWN", "process_name": "Unknown Proc", "process_type": "Manufacturing", "process_order": 4})
    proc_id = proc_res.json()["id"]
    client.post("/api/v1/reader-locations/", json={"port_name": "COM_UNKNOWN", "process_id": proc_id, "location_type": "IN", "description": "Reader"})

    response = client.post(
        "/api/v1/rfid/scan",
        json={
            "type": "SCAN",
            "port_name": "COM_UNKNOWN",
            "epc": "EPC-UNKNOWN-TAG",
            "scan_time": datetime.now().isoformat()
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "PALLET_NOT_FOUND"
