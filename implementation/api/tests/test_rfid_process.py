from fastapi.testclient import TestClient
from datetime import datetime

import uuid

def test_rfid_scan_in_success(client: TestClient):
    uid = str(uuid.uuid4())[:8]
    # 1. Setup Data
    # Process
    proc_res = client.post("/api/v1/processes/", json={"process_code": f"PROC-SCAN-{uid}", "process_name": "Scan Process", "process_type": "Manufacturing", "process_order": 990})
    proc_id = proc_res.json()["id"]

    # Reader (IN)
    client.post("/api/v1/reader-locations/", json={"port_name": f"COM_IN_{uid}", "process_id": proc_id, "location_type": "IN", "description": "IN Reader"})

    # Item & Lot & Pallet
    item_res = client.post("/api/v1/items/", json={"item_code": f"ITEM-SCAN-{uid}", "item_name": "Scan Item", "item_type": "RAW"})
    item_id = item_res.json()["id"]
    
    lot_res = client.post("/api/v1/lots/receiving", json={
        "item_id": item_id, 
        "quantity": 100, 
        "production_date": "2023-12-16"
    })
    lot_id = lot_res.json()["id"]
    
    # Pallet
    epc = f"EPC-SCAN-{uid}"
    pallet_res = client.post("/api/v1/pallets", json={"pallet_no": f"PAL-SCAN-{uid}", "rfid_epc": epc, "status": "Empty"})
    pallet_id = pallet_res.json()["id"]
    
    # Link Pallet to Lot (Status -> Stock)
    link_res = client.put(f"/api/v1/pallets/{pallet_id}/link-lot", json={"lot_id": lot_id})
    assert link_res.status_code == 200
    
    # Scan at IN (Stock -> Consuming)
    response = client.post(
        "/api/v1/rfid/scan",
        json={
            "type": "SCAN",
            "port_name": f"COM_IN_{uid}",
            "epc": epc,
            "scan_time": datetime.now().isoformat()
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # IN 스캔 -> Consuming (투입)
    assert data["pallet"]["current_status"] == "Consuming"

def test_rfid_scan_unknown_tag(client: TestClient):
    uid = str(uuid.uuid4())[:8]
    # Setup Reader First
    proc_res = client.post("/api/v1/processes/", json={"process_code": f"PROC-UNKN-{uid}", "process_name": "Unknown Proc", "process_type": "Manufacturing", "process_order": 999})
    proc_id = proc_res.json()["id"]
    client.post("/api/v1/reader-locations/", json={"port_name": f"COM_UNKN_{uid}", "process_id": proc_id, "location_type": "IN", "description": "Reader"})

    response = client.post(
        "/api/v1/rfid/scan",
        json={
            "type": "SCAN",
            "port_name": f"COM_UNKN_{uid}",
            "epc": f"EPC-UNKN-{uid}",
            "scan_time": datetime.now().isoformat()
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "PALLET_NOT_FOUND"
