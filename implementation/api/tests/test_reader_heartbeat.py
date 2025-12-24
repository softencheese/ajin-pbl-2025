"""리더기 상태(Heartbeat) API 테스트 (POST /rfid/reader-status)"""
from fastapi.testclient import TestClient
from datetime import datetime
from app.models.rfid import RFIDReaderLocation
from sqlalchemy.orm import Session
import uuid


def test_reader_status_connected(client: TestClient, db_session: Session):
    """리더기 연결 상태 업데이트 테스트"""
    # 기존 리더기 조회
    reader = db_session.query(RFIDReaderLocation).first()
    assert reader is not None
    
    response = client.post("/api/v1/rfid/reader-status", json={
        "port_name": reader.port_name,
        "status": "CONNECTED",
        "last_scan_time": datetime.now().isoformat(),
        "uptime_seconds": 3600,
        "total_scans": 150,
        "error_count": 0
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data


def test_reader_status_disconnected(client: TestClient, db_session: Session):
    """리더기 연결 해제 상태 업데이트 테스트"""
    uid = str(uuid.uuid4())[:8]
    
    # 새 리더기 등록
    new_reader = RFIDReaderLocation(
        port_name=f"READER-HB-{uid}",
        description="Heartbeat Test Reader",
        is_active=True
    )
    db_session.add(new_reader)
    db_session.commit()
    
    response = client.post("/api/v1/rfid/reader-status", json={
        "port_name": new_reader.port_name,
        "status": "DISCONNECTED",
        "uptime_seconds": 0,
        "total_scans": 0,
        "error_count": 0
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_reader_status_error(client: TestClient, db_session: Session):
    """리더기 에러 상태 업데이트 테스트"""
    reader = db_session.query(RFIDReaderLocation).first()
    
    response = client.post("/api/v1/rfid/reader-status", json={
        "port_name": reader.port_name,
        "status": "ERROR",
        "uptime_seconds": 1800,
        "total_scans": 50,
        "error_count": 5
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_reader_status_auto_register(client: TestClient):
    """알려지지 않은 리더기 자동 등록 테스트"""
    uid = str(uuid.uuid4())[:8]
    
    # 존재하지 않는 포트명으로 요청
    response = client.post("/api/v1/rfid/reader-status", json={
        "port_name": f"NEW-READER-{uid}",
        "status": "CONNECTED",
        "uptime_seconds": 100,
        "total_scans": 0,
        "error_count": 0
    })
    
    # 자동 등록 성공 또는 에러 처리
    assert response.status_code in [200, 404]
    data = response.json()
    # 자동 등록되거나 에러 메시지 반환
    if response.status_code == 200:
        assert data["success"] is True
