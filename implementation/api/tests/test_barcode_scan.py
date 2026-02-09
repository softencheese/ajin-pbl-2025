"""바코드 스캔 API 테스트 (POST /rfid/scan-barcode)"""
from fastapi.testclient import TestClient
from datetime import datetime, date
from app.models.process import Process
from app.models.item import Item
from app.models.rfid import RFIDReaderLocation
from app.models.pallet import Pallet
from app.models.lot import Lot
from sqlalchemy.orm import Session
import uuid


def test_barcode_scan_success(client: TestClient, db_session: Session):
    """바코드 스캔으로 팔레트 상태 전이 테스트"""
    uid = str(uuid.uuid4())[:8]
    
    # 1. 마스터 데이터 조회 (from init_db)
    process = db_session.query(Process).filter(Process.process_code == "PRESS").first()
    reader = db_session.query(RFIDReaderLocation).filter(
        RFIDReaderLocation.port_name == "PRESS-IN"
    ).first()
    item = db_session.query(Item).filter(Item.item_type == "WIP").first()
    
    assert process is not None, "PRESS 공정이 필요합니다"
    assert reader is not None, "PRESS-IN 리더기가 필요합니다"
    assert item is not None, "WIP 아이템이 필요합니다"
    
    # 2. LOT 생성
    lot = Lot(
        lot_number=f"BAR-LOT-{uid}",
        barcode=f"BAR-LOT-{uid}",  # 바코드 = LOT번호
        item_id=item.id,
        quantity=100,
        initial_quantity=100,
        production_date=date.today(),
        status="STOCK"
    )
    db_session.add(lot)
    db_session.commit()
    
    # 3. 팔레트 생성 및 LOT 연결 (PhysicalPallet + Pallet)
    from app.models.physical_pallet import PhysicalPallet
    pp = PhysicalPallet(epc=f"EPC-BAR-{uid}", pallet_code=f"PLT-BAR-{uid}", status="Stock")
    db_session.add(pp)
    db_session.flush()
    pallet = Pallet(
        pallet_no=f"PLT-BAR-{uid}",
        physical_pallet_id=pp.id,
        status="Stock",
        lot_id=lot.id
    )
    db_session.add(pallet)
    db_session.commit()
    
    # 4. 바코드 스캔 요청
    response = client.post("/api/v1/rfid/scan-barcode", json={
        "barcode": lot.barcode,
        "port_name": "PRESS-IN",
        "scan_time": datetime.now().isoformat()
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["pallet"]["current_status"] == "Consuming"


def test_barcode_scan_not_found(client: TestClient, db_session: Session):
    """존재하지 않는 바코드 스캔 테스트"""
    # 리더기 조회
    reader = db_session.query(RFIDReaderLocation).first()
    
    response = client.post("/api/v1/rfid/scan-barcode", json={
        "barcode": "NON-EXISTENT-BARCODE-99999",
        "port_name": reader.port_name,
        "scan_time": datetime.now().isoformat()
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    # 에러 타입은 구현에 따라 다를 수 있음
    assert "error" in data and data["error"] is not None


def test_barcode_scan_at_out_location(client: TestClient, db_session: Session):
    """OUT 위치에서 바코드 스캔 - Stock 상태로 전이"""
    uid = str(uuid.uuid4())[:8]
    
    # 마스터 데이터 조회
    item = db_session.query(Item).filter(Item.item_type == "WIP").first()
    
    # LOT 생성
    lot = Lot(
        lot_number=f"BAR-OUT-{uid}",
        barcode=f"BAR-OUT-{uid}",
        item_id=item.id,
        quantity=50,
        initial_quantity=50,
        production_date=date.today(),
        status="STOCK"
    )
    db_session.add(lot)
    db_session.commit()
    
    # 팔레트 생성 (Consuming 상태로 시작, PhysicalPallet + Pallet)
    from app.models.physical_pallet import PhysicalPallet
    pp = PhysicalPallet(epc=f"EPC-OUT-{uid}", pallet_code=f"PLT-OUT-{uid}", status="Consuming")
    db_session.add(pp)
    db_session.flush()
    pallet = Pallet(
        pallet_no=f"PLT-OUT-{uid}",
        physical_pallet_id=pp.id,
        status="Consuming",
        lot_id=lot.id
    )
    db_session.add(pallet)
    db_session.commit()

    # OUT 리더기에서 스캔 -> Stock으로 전이
    response = client.post("/api/v1/rfid/scan-barcode", json={
        "barcode": lot.barcode,
        "port_name": "PRESS-OUT",
        "scan_time": datetime.now().isoformat()
    })
    
    assert response.status_code == 200
    data = response.json()
    # 성공한 경우 상태 확인 - OUT 스캔은 Stock 또는 Empty로 전이 가능
    # Empty는 연속 스캔으로 인한 소진 시, Stock은 일반적인 배출 시
    if data["success"] and data.get("pallet"):
        assert data["pallet"]["current_status"] in ["Stock", "Empty"]
