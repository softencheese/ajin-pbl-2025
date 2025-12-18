from fastapi.testclient import TestClient

def test_master_data_conflict(client: TestClient):
    # 1. Create Process
    process_data = {
        "process_code": "DUPLICATE_PROC",
        "process_name": "Dup Process",
        "process_order": 100
    }
    # First creation - Expect 200 or 201
    response = client.post("/api/v1/processes/", json=process_data)
    assert response.status_code in [200, 201]

    # Second creation - Expect 409 Conflict
    response = client.post("/api/v1/processes/", json=process_data)
    assert response.status_code == 409
    assert response.json()["detail"] == "Process code already exists"

def test_full_process_flow(client: TestClient):
    # 1. Setup Master Data
    # Create Process
    proc_res = client.post("/api/v1/processes/", json={
        "process_code": "FLOW_PROC", "process_name": "Flow Proc", "process_order": 1
    })
    process_id = proc_res.json()["id"]

    # Create Item
    item_res = client.post("/api/v1/items/", json={
        "item_code": "FLOW_ITEM", "item_name": "Flow Item", "item_type": "RAW", "unit": "EA"
    })
    item_id = item_res.json()["id"]

    # 2. Create Pallet
    pal_res = client.post("/api/v1/pallets/", json={
        "pallet_no": "FLOW_PLT_001", "rfid_epc": "FLOW_EPC_001"
    })
    assert pal_res.status_code in [200, 201]
    pallet_id = pal_res.json()["id"]

    # 3. Create LOT (Receiving)
    lot_res = client.post("/api/v1/lots/receiving", json={
        "item_id": item_id, "quantity": 100, "production_date": "2024-01-01", "supplier": "Test"
    })
    assert lot_res.status_code in [200, 201]
    lot_data = lot_res.json()
    lot_id = lot_data["id"]
    lot_number = lot_data["lot_number"]

    # 4. Link LOT to Pallet
    link_res = client.put(f"/api/v1/pallets/{pallet_id}/link-lot", json={"lot_id": lot_id})
    assert link_res.status_code == 200
    assert link_res.json()["lot_number"] == lot_number

    # 5. RFID Scan (Start Process)
    scan_data = {
        "epc": "FLOW_EPC_001",
        "port_name": "UNKNOWN_PORT", # To trigger logic
        "scan_time": "2024-01-01T12:00:00Z",
        "reader_info": {}
    }
    # Note: Without a registered ReaderLocation, scan might fail or default. 
    # Let's verify scan endpoint fits.
    scan_res = client.post("/api/v1/rfid/scan", json=scan_data)
    assert scan_res.status_code == 200
    # Check status change (Depends on state machine logic, might stay in Stock if reader not mapped)
