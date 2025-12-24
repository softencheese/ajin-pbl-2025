from fastapi.testclient import TestClient

def test_not_found_error(client: TestClient):
    """404 Not Found 테스트"""
    # Invalid Lot ID
    response = client.get("/api/v1/lots/999999")
    assert response.status_code == 404
    
    # Invalid Pallet ID
    response = client.get("/api/v1/pallets/999999")
    assert response.status_code == 404

def test_bad_request_error(client: TestClient):
    """400 Bad Request 테스트 (필수 필드 누락)"""
    # Create Item without code
    response = client.post("/api/v1/items/", json={
        "item_name": "No Code Item",
        "item_type": "RAW"
    })
    # FastAPI Validate Error usually 422
    assert response.status_code == 422 
    
def test_validation_error_types(client: TestClient):
    """422 Validation Error 테스트 (타입 불일치)"""
    # Quantity as string
    response = client.post("/api/v1/lots/receiving", json={
        "item_id": 1,
        "quantity": "Not a number"
    })
    assert response.status_code == 422

# Conflict (409) is tested in master_data tests
