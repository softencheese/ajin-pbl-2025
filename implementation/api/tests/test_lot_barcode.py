from fastapi.testclient import TestClient

def test_lot_number_generation_and_barcode(client: TestClient):
    """
    Verify LOT number format (YYMMDD + PP + SSSS) and Barcode handling.
    """
    # 1. Setup Data: Item (RAW)
    item_res = client.post("/api/v1/items/", json={
        "item_code": "TEST-BARCODE-ITEM", 
        "item_name": "Barcode Test Item", 
        "item_type": "RAW"
    })
    assert item_res.status_code == 200 or item_res.status_code == 201
    item_id = item_res.json()["id"]

    # 2. Case A: Create LOT *without* barcode (should default to lot_number)
    # Using 'receiving' endpoint as it's simpler (Process 00)
    res_a = client.post("/api/v1/lots/receiving", json={
        "item_id": item_id,
        "quantity": 100,
        "production_date": "2024-12-18", # Fixed date for predictable prefix
        "notes": "No barcode provided"
    })
    
    assert res_a.status_code == 201
    data_a = res_a.json()
    
    # Check LOT Number Format: 241218 + 00 + SSSS
    lot_num_a = data_a["lot_number"]
    assert len(lot_num_a) == 12
    assert lot_num_a.startswith("24121800")
    
    # Check Barcode Default
    assert data_a["barcode"] == lot_num_a, "Barcode should default to LOT Number if not provided"
    
    # 3. Case B: Create LOT *with* explicit barcode
    res_b = client.post("/api/v1/lots/receiving", json={
        "item_id": item_id,
        "quantity": 200,
        "production_date": "2024-12-18",
        "barcode": "MY-CUSTOM-BARCODE-123"
    })
    
    assert res_b.status_code == 201
    data_b = res_b.json()
    
    # Check LOT Number Format
    lot_num_b = data_b["lot_number"]
    assert len(lot_num_b) == 12
    assert lot_num_b.startswith("24121800")
    assert lot_num_b != lot_num_a, "Should be a new LOT number"
    
    # Check Barcode
    assert data_b["barcode"] == "MY-CUSTOM-BARCODE-123", "Should use provided barcode"

def test_production_lot_barcode(client: TestClient):
    """
    Verify LOT/Barcode for Production Process (Process ID > 0)
    """
    # 1. Setup Item (PRODUCT) and Process
    item_res = client.post("/api/v1/items/", json={
        "item_code": "TEST-PROD-ITEM", "item_name": "Prod Item", "item_type": "PRODUCT"
    })
    item_id = item_res.json()["id"]
    
    proc_res = client.post("/api/v1/processes", json={
        "process_code": "TEST_PROC", 
        "process_name": "Test Process", 
        "process_order": 5, 
        "production_line": "Line 5"
    })
    # If exists, get it (handle 409 or similar if needed, but clean env should be fine)
    # Assuming clean DB from 'make test' setup usually, but let's handle if it fails?
    # Actually 'make test' usually doesn't reset DB unless fixture does. 
    # Let's assume typical test isolation.
    
    if proc_res.status_code == 200 or proc_res.status_code == 201:
        process_id = proc_res.json()["id"]
    else:
        # Fallback: try to find existing or list
        procs = client.get("/api/v1/processes").json()
        process_id = procs[0]["id"]
        # Ensure it has order > 0 for this test or just use its order
        process_order = procs[0]["process_order"]

    # If we created it:
    if proc_res.status_code in [200, 201]:
         process_order = 5

    # 2. Create Production LOT
    # Note: Production lot creation usually requires 'input_lots' if strict CHECK, 
    # but based on `lots.py` code, `input_lots` is optional in schema (List[LotInput] = None).
    # Let's try without inputs for simplicity of testing generated number.
    
    res = client.post("/api/v1/lots", json={
        "item_id": item_id,
        "process_id": process_id,
        "quantity": 50,
        "production_date": "2024-12-18",
        # No barcode
    })
    
    assert res.status_code == 201
    data = res.json()
    
    # Expected Prefix: 241218 + 05 (or whatever process_order is)
    prefix_expected = f"241218{process_order:02}"
    assert data["lot_number"].startswith(prefix_expected)
    assert data["barcode"] == data["lot_number"]
