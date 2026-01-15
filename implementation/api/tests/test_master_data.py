from fastapi.testclient import TestClient


# ============================================
# Process Tests
# ============================================

import uuid

import random

def test_create_process(client: TestClient):
    uid = str(uuid.uuid4())[:8]
    order = random.randint(100, 900)
    response = client.post(
        "/api/v1/processes/",
        json={
            "process_code": f"PROC-{uid}",
            "process_name": "Test Process",
            "process_order": order,
        }
    )
    if response.status_code == 409:
        print(f"Conflict Error Body: {response.json()}")
    assert response.status_code == 200 or response.status_code == 201, f"Status: {response.status_code}, Body: {response.text}"
    data = response.json()
    assert data["process_code"] == f"PROC-{uid}"
    assert "id" in data

# ... (중략) ...

def test_create_reader_location(client: TestClient):
    # First create a process to link to
    uid = str(uuid.uuid4())[:8]
    order = random.randint(100, 900)
    proc_res = client.post("/api/v1/processes/", json={
        "process_code": f"READER-PROC-{uid}", 
        "process_name": "Reader Process",
        "process_order": order
    })
    if proc_res.status_code == 409:
        print(f"Reader Proc Conflict: {proc_res.json()}")
    
    assert proc_res.status_code in [200, 201], f"Proc Create Failed: {proc_res.text}"
    process_id = proc_res.json()["id"]

    response = client.post(
        "/api/v1/reader-locations/",
        json={
            "port_name": f"COM-{uid}",
            "process_id": process_id,
            "location_type": "IN",
            "description": "Test Reader"
        }
    )
    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert data["port_name"] == f"COM-{uid}"
    assert data["location_type"] == "IN"


def test_list_reader_locations(client: TestClient):
    """목록 조회 테스트 - 직렬화 에러 검출"""
    response = client.get("/api/v1/reader-locations")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)

def test_check_handheld_reader(client: TestClient):
    """휴대용 리더기 등록 확인 (from init_db)"""
    response = client.get("/api/v1/reader-locations")
    data = response.json()
    items = data["items"]
    
    handheld = next((r for r in items if r["port_name"] == "HANDHELD-01"), None)
    assert handheld is not None
    assert handheld["description"] == "휴대용 재고 확인 리더기"
    assert handheld["process_id"] is None
    assert handheld["location_type"] is None
