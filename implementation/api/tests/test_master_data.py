from fastapi.testclient import TestClient


# ============================================
# Process Tests
# ============================================

def test_create_process(client: TestClient):
    response = client.post(
        "/api/v1/processes/",
        json={
            "process_code": "PROC-001",
            "process_name": "Test Process",
            "process_order": 1,
        }
    )
    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert data["process_code"] == "PROC-001"
    assert "id" in data


def test_list_processes(client: TestClient):
    """목록 조회 테스트 - 직렬화 에러 검출"""
    # 먼저 데이터 생성
    client.post("/api/v1/processes/", json={
        "process_code": "LIST-PROC", "process_name": "List Test", "process_order": 99
    })
    
    response = client.get("/api/v1/processes")
    assert response.status_code == 200
    data = response.json()
    # 페이지네이션 응답 구조 확인
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert isinstance(data["items"], list)


def test_get_process_detail(client: TestClient):
    """상세 조회 테스트"""
    create_res = client.post("/api/v1/processes/", json={
        "process_code": "DETAIL-PROC", "process_name": "Detail Test", "process_order": 98
    })
    proc_id = create_res.json()["id"]
    
    response = client.get(f"/api/v1/processes/{proc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["process_code"] == "DETAIL-PROC"


# ============================================
# Item Tests
# ============================================

def test_create_item(client: TestClient):
    response = client.post(
        "/api/v1/items/",
        json={
            "item_code": "ITEM-001",
            "item_name": "Test Item",
            "item_type": "RAW",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["item_code"] == "ITEM-001"


def test_list_items(client: TestClient):
    """목록 조회 테스트 - 직렬화 에러 검출"""
    client.post("/api/v1/items/", json={
        "item_code": "LIST-ITEM", "item_name": "List Test", "item_type": "RAW"
    })
    
    response = client.get("/api/v1/items")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


# ============================================
# Reader Location Tests
# ============================================

def test_create_reader_location(client: TestClient):
    # First create a process to link to
    proc_res = client.post("/api/v1/processes/", json={
        "process_code": "READER-PROC", 
        "process_name": "Reader Process",
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


def test_list_reader_locations(client: TestClient):
    """목록 조회 테스트 - 직렬화 에러 검출"""
    response = client.get("/api/v1/reader-locations")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
