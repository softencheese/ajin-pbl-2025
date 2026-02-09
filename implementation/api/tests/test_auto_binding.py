from datetime import datetime
from app.models.process import Process
from app.models.item import Item
from app.models.rfid import RFIDReaderLocation
from app.models.pallet import Pallet
from app.models.lot import Lot
from app.models.physical_pallet import PhysicalPallet

def test_auto_binding_at_out_location(client, db_session):
    """생산 공정(OUT)에서 미등록 EPC 스캔 시 자동 바인딩 테스트"""
    
    # 1. 테스트 상항 설정
    # COM01 공정의 OUT 리더기 조회
    reader_out = db_session.query(RFIDReaderLocation).filter(
        RFIDReaderLocation.port_name == "COM01-OUT"
    ).first()
    assert reader_out is not None
    assert reader_out.location_type == "OUT"
    
    # 가상 팔레트 생성 (실물 연결 안됨)
    # 1.1 품목 및 LOT 생성
    item = db_session.query(Item).first()
    lot = Lot(
        lot_number="LOT-AUTO-BIND-TEST",
        item_id=item.id,
        quantity=50,
        initial_quantity=50,
        production_date=datetime.now().date(),
        status="WAIT"
    )
    db_session.add(lot)
    db_session.flush()
    
    # 1.2 가상 팔레트 생성 (실물 연결 X)
    virtual_pallet = Pallet(
        pallet_no="PLT-AUTO-BIND-001",
        physical_pallet_id=None, # 실물 연결 안됨
        lot_id=lot.id,
        quantity=50,
        status="Generated",
        current_process_id=reader_out.process_id
    )
    db_session.add(virtual_pallet)
    db_session.commit()
    
    # 2. 미등록 EPC로 스캔 요청
    test_epc = "E280-TEST-AUTO-BIND"
    
    # 먼저 해당 EPC가 없는지 확인
    exists = db_session.query(PhysicalPallet).filter(PhysicalPallet.epc == test_epc).first()
    assert exists is None
    
    response = client.post("/api/v1/rfid/scan", json={
        "epc": test_epc,
        "port_name": reader_out.port_name,
        "scan_time": datetime.now().isoformat()
    })
    
    # 3. 결과 검증
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # 3.1 DB에 PhysicalPallet가 생성되었는지 확인
    db_session.expire_all()
    pp = db_session.query(PhysicalPallet).filter(PhysicalPallet.epc == test_epc).first()
    assert pp is not None
    
    # 3.2 가상 팔레트에 실물 팔레트가 연결되었는지 확인
    updated_pallet = db_session.query(Pallet).filter(Pallet.pallet_no == "PLT-AUTO-BIND-001").first()
    assert updated_pallet.physical_pallet_id == pp.id
    assert updated_pallet.tag_status == "IN_USE"
    
    # 3.3 상태 전이가 정상적으로 일어났는지 확인 (Generated -> Producing)
    # StateMachine에 의해 Generated 상태에서 OUT 스캔 시 Producing으로 변경되어야 함
    assert updated_pallet.status == "Producing"
    
    # 3.4 바인딩된 팔레트 정보가 응답에 포함되었는지 확인
    assert data["pallet"]["pallet_no"] == "PLT-AUTO-BIND-001"
    assert data["pallet"]["current_status"] == "Producing"

def test_auto_binding_fail_at_in_location(client, db_session):
    """투입 공정(IN)에서 미등록 EPC 스캔 시에는 자동 바인딩이 되지 않고 에러가 발생해야 함"""
    
    # 1. SHEARING 공정의 IN 리더기 조회 (또는 다른 IN 리더기)
    reader_in = db_session.query(RFIDReaderLocation).filter(
        RFIDReaderLocation.location_type == "IN"
    ).first()
    assert reader_in is not None
    
    # 2. 미등록 EPC로 IN 스캔 요청
    test_epc_in = "E280-TEST-FAIL-IN"
    
    response = client.post("/api/v1/rfid/scan", json={
        "epc": test_epc_in,
        "port_name": reader_in.port_name,
        "scan_time": datetime.now().isoformat()
    })
    
    # 3. 결과 검증
    assert response.status_code == 200 # API 자체는 200 (에러 응답 포함)
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "PALLET_NOT_FOUND" 
