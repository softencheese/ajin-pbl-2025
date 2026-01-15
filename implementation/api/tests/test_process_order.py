"""공정 순서 변경 테스트 (PUT /processes/{id}/order)"""
from fastapi.testclient import TestClient
from app.models.process import Process
from sqlalchemy.orm import Session
import uuid


def test_update_process_order_move_up(client: TestClient, db_session: Session):
    """공정 순서 위로 이동 테스트"""
    uid = str(uuid.uuid4())[:8]
    
    # 테스트용 공정 2개 생성
    proc1 = Process(
        process_code=f"ORD1-{uid}",
        process_name="순서 테스트 1",
        process_order=801
    )
    proc2 = Process(
        process_code=f"ORD2-{uid}",
        process_name="순서 테스트 2",
        process_order=802
    )
    db_session.add_all([proc1, proc2])
    db_session.commit()
    
    # proc2를 801로 이동 (위로)
    response = client.put(f"/api/v1/processes/{proc2.id}/order", json={
        "new_order": 801
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["process_order"] == 801
    
    # proc1은 802가 되어야 함 - 재조회로 확인
    proc1_updated = db_session.query(Process).filter(Process.id == proc1.id).first()
    assert proc1_updated.process_order == 802


def test_update_process_order_move_down(client: TestClient, db_session: Session):
    """공정 순서 아래로 이동 테스트"""
    uid = str(uuid.uuid4())[:8]
    
    proc1 = Process(
        process_code=f"ORD3-{uid}",
        process_name="아래 이동 1",
        process_order=901
    )
    proc2 = Process(
        process_code=f"ORD4-{uid}",
        process_name="아래 이동 2",
        process_order=902
    )
    db_session.add_all([proc1, proc2])
    db_session.commit()
    
    # proc1을 902로 이동 (아래로)
    response = client.put(f"/api/v1/processes/{proc1.id}/order", json={
        "new_order": 902
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["process_order"] == 902
    
    # proc2는 901이 되어야 함 - 재조회로 확인
    proc2_updated = db_session.query(Process).filter(Process.id == proc2.id).first()
    assert proc2_updated.process_order == 901


def test_update_process_order_not_found(client: TestClient):
    """존재하지 않는 공정 순서 변경 시 404 에러"""
    response = client.put("/api/v1/processes/999999/order", json={
        "new_order": 1
    })
    assert response.status_code == 404


def test_get_process_detail(client: TestClient, db_session: Session):
    """공정 상세 조회 테스트 (GET /processes/{id})"""
    process = db_session.query(Process).first()
    assert process is not None
    
    response = client.get(f"/api/v1/processes/{process.id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == process.id
    assert data["process_code"] == process.process_code
    assert data["process_name"] == process.process_name
    assert "process_order" in data


def test_update_process(client: TestClient, db_session: Session):
    """공정 수정 테스트 (PUT /processes/{id})"""
    uid = str(uuid.uuid4())[:8]
    
    # 테스트용 공정 생성
    proc = Process(
        process_code=f"UPD-{uid}",
        process_name="수정 전",
        process_order=950
    )
    db_session.add(proc)
    db_session.commit()
    
    # 수정
    response = client.put(f"/api/v1/processes/{proc.id}", json={
        "process_name": "수정 후 이름",
        "production_line": "LINE-A"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["process_name"] == "수정 후 이름"
    assert data["production_line"] == "LINE-A"


def test_delete_process_success(client: TestClient, db_session: Session):
    """공정 삭제 테스트 (DELETE /processes/{id}) - 연결 데이터 없는 경우"""
    uid = str(uuid.uuid4())[:8]
    
    # 독립적인 공정 생성
    proc = Process(
        process_code=f"DEL-{uid}",
        process_name="삭제 대상",
        process_order=999
    )
    db_session.add(proc)
    db_session.commit()
    proc_id = proc.id
    
    response = client.delete(f"/api/v1/processes/{proc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # 삭제 확인
    deleted = db_session.query(Process).filter(Process.id == proc_id).first()
    assert deleted is None


def test_delete_process_with_readers(client: TestClient, db_session: Session):
    """리더기가 연결된 공정 삭제 시 409 에러"""
    # init_db로 생성된 공정 중 리더기가 연결된 것
    from app.models.rfid import RFIDReaderLocation
    
    reader = db_session.query(RFIDReaderLocation).filter(
        RFIDReaderLocation.process_id.isnot(None)
    ).first()
    
    if reader:
        response = client.delete(f"/api/v1/processes/{reader.process_id}")
        assert response.status_code == 409
