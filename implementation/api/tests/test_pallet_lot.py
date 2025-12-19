from fastapi.testclient import TestClient

def test_create_pallet(client: TestClient):
    response = client.post(
        "/api/v1/pallets", # Remove trailing slash
        json={
            "pallet_no": "PAL-001",
            "rfid_epc": "EPC-0000000001",
            "status": "Empty"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["pallet_no"] == "PAL-001"
    assert data["rfid_epc"] == "EPC-0000000001"

def test_create_receiving_lot(client: TestClient):
    # Need an Item first
    item_res = client.post("/api/v1/items/", json={
        "item_code": "COIL-TEST", "item_name": "Steel Coil", "item_type": "RAW"
    })
    item_id = item_res.json()["id"]

    response = client.post(
        "/api/v1/lots/receiving",
        json={
            "item_id": item_id,
            "quantity": 1000,
            "production_date": "2023-12-16"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 1000
    # New format: YYMMDD + 00 + SSSS -> 12 digits
    assert len(data["lot_number"]) == 12
    assert data["lot_number"].isdigit()
    assert data["lot_number"].startswith("23121600")

def test_link_pallet_lot(client: TestClient):
    # Setup Pallet
    p_res = client.post("/api/v1/pallets", json={"pallet_no": "PAL-002", "rfid_epc": "EPC-002", "status": "Empty"})
    pallet_id = p_res.json()["id"]

    # Setup Item & Lot
    i_res = client.post("/api/v1/items/", json={"item_code": "PART-LINK", "item_name": "Part", "item_type": "RAW"})
    item_id = i_res.json()["id"]

    l_res = client.post("/api/v1/lots/receiving", json={
        "item_id": item_id, 
        "quantity": 100, 
        "production_date": "2023-12-16"
    })
    lot_id = l_res.json()["id"]
    lot_no = l_res.json()["lot_number"]

    # Link: PUT /api/v1/pallets/{id}/link-lot
    response = client.put(f"/api/v1/pallets/{pallet_id}/link-lot", json={"lot_id": lot_id})
    
    assert response.status_code == 200
    data = response.json()
    assert data["lot_number"] == lot_no
    assert data["status"] == "Stock" # Assuming Stock status after linking
