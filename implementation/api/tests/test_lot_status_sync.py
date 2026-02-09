from fastapi.testclient import TestClient
from datetime import datetime
import uuid

def test_lot_status_sync_on_scan(client: TestClient):
    uid = str(uuid.uuid4())[:8]
    
    # 1. Setup Data
    # Process
    proc_res = client.post("/api/v1/processes/", json={
        "process_code": f"SYNC-{uid}", 
        "process_name": "Sync Process", 
        "process_type": "Manufacturing", 
        "process_order": 100
    })
    proc_id = proc_res.json()["id"]

    # Readers
    client.post("/api/v1/reader-locations/", json={"port_name": f"PORT_IN_{uid}", "process_id": proc_id, "location_type": "IN", "description": "IN"})
    client.post("/api/v1/reader-locations/", json={"port_name": f"PORT_OUT_{uid}", "process_id": proc_id, "location_type": "OUT", "description": "OUT"})

    # Item
    item_res = client.post("/api/v1/items/", json={
        "item_code": f"ITEM-SYNC-{uid}", 
        "item_name": "Sync Item", 
        "item_type": "WIP"
    })
    item_id = item_res.json()["id"]

    # 2. Test Producing Flow (WAIT -> PROCESS -> STOCK)
    # Create LOT (will create Pallets automatically)
    lot_res = client.post("/api/v1/lots", json={
        "item_id": item_id,
        "process_id": proc_id,
        "quantity": 100,
        "production_date": "2024-02-08",
        "pallet_capacity": 50  # Should create 2 pallets
    })
    lot_data = lot_res.json()
    lot_id = lot_data["id"]
    assert lot_data["status"] == "WAIT"

    # Get Pallets
    pallets_res = client.get(f"/api/v1/pallets?lot_id={lot_id}")
    pallets = pallets_res.json()["items"]
    assert len(pallets) == 2
    
    # Register physical EPCs for pallets
    epc1 = f"EPC1-{uid}"
    epc2 = f"EPC2-{uid}"
    client.put(f"/api/v1/pallets/{pallets[0]['id']}", json={"rfid_epc": epc1})
    client.put(f"/api/v1/pallets/{pallets[1]['id']}", json={"rfid_epc": epc2})

    # Step A: Scan 1st pallet at OUT (Empty -> Producing)
    # LOT status should become PROCESS
    client.post("/api/v1/rfid/scan", json={
        "type": "SCAN", "port_name": f"PORT_OUT_{uid}", "epc": epc1, "scan_time": datetime.now().isoformat()
    })
    
    lot_verify = client.get(f"/api/v1/lots/{lot_id}").json()
    assert lot_verify["status"] == "PROCESS"

    # Step B: Scan 1st pallet at OUT again (Producing -> Stock)
    # LOT status should still be PROCESS (since 2nd pallet is still WAIT/Empty)
    client.post("/api/v1/rfid/scan", json={
        "type": "SCAN", "port_name": f"PORT_OUT_{uid}", "epc": epc1, "scan_time": datetime.now().isoformat()
    })
    lot_verify = client.get(f"/api/v1/lots/{lot_id}").json()
    assert lot_verify["status"] == "PROCESS"

    # Step C: Scan 2nd pallet at OUT (Empty -> Producing -> Stock)
    # After last pallet is Stock, LOT status should become STOCK
    client.post("/api/v1/rfid/scan", json={
        "type": "SCAN", "port_name": f"PORT_OUT_{uid}", "epc": epc2, "scan_time": datetime.now().isoformat()
    })
    client.post("/api/v1/rfid/scan", json={
        "type": "SCAN", "port_name": f"PORT_OUT_{uid}", "epc": epc2, "scan_time": datetime.now().isoformat()
    })
    lot_verify = client.get(f"/api/v1/lots/{lot_id}").json()
    assert lot_verify["status"] == "STOCK"

    # 3. Test Consuming Flow (STOCK -> PROCESS -> CONSUMED)
    # Step D: Scan 1st pallet at IN (Stock -> Consuming)
    # LOT status should become PROCESS
    client.post("/api/v1/rfid/scan", json={
        "type": "SCAN", "port_name": f"PORT_IN_{uid}", "epc": epc1, "scan_time": datetime.now().isoformat()
    })
    lot_verify = client.get(f"/api/v1/lots/{lot_id}").json()
    assert lot_verify["status"] == "PROCESS"

    # Step E: Scan 1st pallet at IN again (Consuming -> Deregistered)
    # LOT status should still be PROCESS
    client.post("/api/v1/rfid/scan", json={
        "type": "SCAN", "port_name": f"PORT_IN_{uid}", "epc": epc1, "scan_time": datetime.now().isoformat()
    })
    lot_verify = client.get(f"/api/v1/lots/{lot_id}").json()
    assert lot_verify["status"] == "PROCESS"

    # Step F: Scan 2nd pallet at IN (Stock -> Consuming -> Deregistered)
    # After last pallet is Deregistered, LOT status should become CONSUMED
    client.post("/api/v1/rfid/scan", json={
        "type": "SCAN", "port_name": f"PORT_IN_{uid}", "epc": epc2, "scan_time": datetime.now().isoformat()
    })
    client.post("/api/v1/rfid/scan", json={
        "type": "SCAN", "port_name": f"PORT_IN_{uid}", "epc": epc2, "scan_time": datetime.now().isoformat()
    })
    lot_verify = client.get(f"/api/v1/lots/{lot_id}").json()
    assert lot_verify["status"] == "CONSUMED"
