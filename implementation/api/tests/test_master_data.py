from fastapi.testclient import TestClient

def test_create_process(client: TestClient):
    response = client.post(
        "/api/v1/processes/",
        json={
            "process_code": "PROC-001",
            "process_name": "Test Process",
            "process_type": "Manufacturing",
            "process_order": 1,
            "description": "Test"
        }
    )
    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert data["process_code"] == "PROC-001"
    assert "id" in data

def test_create_item(client: TestClient):
    response = client.post(
        "/api/v1/items/",
        json={
            "item_code": "ITEM-001",
            "item_name": "Test Item",
            "item_type": "RAW",
            "unit": "kg",
            "description": "Test Material"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["item_code"] == "ITEM-001"

def test_create_reader_location(client: TestClient):
    # First create a process to link to
    proc_res = client.post("/api/v1/processes/", json={
        "process_code": "READER-PROC", 
        "process_name": "Reader Process",
        "process_type": "Logistics",
        "process_order": 2
    })
    process_id = proc_res.json()["id"]

    response = client.post(
        "/api/v1/reader-locations/",
        json={
            "port_name": "COM1",
            "process_id": process_id,
            "location_type": "IN",
            "description": "Test Reader"
        }
    )
    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert data["port_name"] == "COM1"
    assert data["location_type"] == "IN"
