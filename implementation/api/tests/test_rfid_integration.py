from datetime import datetime, date
from app.models.process import Process
from app.models.item import Item
from app.models.rfid import RFIDReaderLocation
from app.models.pallet import Pallet
from app.models.lot import Lot
from app.models.lot_genealogy import LotGenealogy

def test_wrong_part_validation(client, db_session):
    """오투입 검증 테스트 (init_db 데이터 활용)"""
    
    # 1. 데이터 조회 (from init_db)
    # PRESS 공정은 WIP만 허용됨 (init_db 설정)
    proc_press = db_session.query(Process).filter(Process.process_code == "PRESS").first()
    reader_press_in = db_session.query(RFIDReaderLocation).filter(RFIDReaderLocation.port_name == "PRESS-IN").first()
    port_name = reader_press_in.port_name
    
    item_raw = db_session.query(Item).filter(Item.item_type == "RAW").first() # RAW Type
    item_wip = db_session.query(Item).filter(Item.item_type == "WIP").first() # WIP Type
    
    assert proc_press
    assert proc_press.allowed_item_types == "WIP"
    assert item_raw
    assert item_wip

    # 2. FAIL Case: RAW Lot -> PRESS (WIP Only)
    # RAW LOT 생성
    lot_raw = Lot(
        lot_number="LOT-TEST-RAW-FAIL",
        item_id=item_raw.id,
        quantity=100,
        initial_quantity=100,
        production_date=date.today(),
        status="STOCK"
    )
    db_session.add(lot_raw)
    db_session.commit()
    
    # Pallet 생성 및 매핑
    pallet_raw = Pallet(
        pallet_no="PLT-TEST-FAIL",
        rfid_epc="EPC-TEST-FAIL",
        status="Stock",
        lot_id=lot_raw.id
    )
    db_session.add(pallet_raw)
    db_session.commit()
    
    # Scan RAW at PRESS-IN
    response = client.post("/api/v1/rfid/scan", json={
        "epc": "EPC-TEST-FAIL",
        "port_name": port_name,
        "scan_time": datetime.now().isoformat()
    })
    
    data = response.json()
    
    # 기대결과: 오투입 에러 (WRONG_PART)
    assert data["success"] is False
    assert data["error"]["type"] == "WRONG_PART"
    
    # 3. SUCCESS Case: WIP Lot -> PRESS
    # WIP LOT 생성
    lot_wip = Lot(
        lot_number="LOT-TEST-WIP-OK",
        item_id=item_wip.id,
        quantity=100,
        initial_quantity=100,
        production_date=date.today(),
        status="STOCK"
    )
    db_session.add(lot_wip)
    db_session.commit()
    
    pallet_wip = Pallet(
        pallet_no="PLT-TEST-OK",
        rfid_epc="EPC-TEST-OK",
        status="Stock",
        lot_id=lot_wip.id
    )
    db_session.add(pallet_wip)
    db_session.commit()
    
    # Scan WIP at PRESS-IN
    response = client.post("/api/v1/rfid/scan", json={
        "epc": "EPC-TEST-OK",
        "port_name": port_name,
        "scan_time": datetime.now().isoformat()
    })
    
    data = response.json()
    assert data["success"] is True

def test_recursive_trace(client, db_session):
    """재귀적 추적 테스트 (init_db 기반 위에 데이터 추가)"""
    
    # 데이터 조회
    proc_shearing = db_session.query(Process).filter(Process.process_code == "SHEARING").first()
    proc_press = db_session.query(Process).filter(Process.process_code == "PRESS").first()
    item_raw = db_session.query(Item).filter(Item.item_type == "RAW").first()
    item_wip = db_session.query(Item).filter(Item.item_type == "WIP").first()

    # Create Genealogy: L1(RAW) -> L2(WIP) -> L3(WIP-2)
    l1 = Lot(lot_number="TRACE-L1", item_id=item_raw.id, quantity=100, initial_quantity=100, production_date=date.today())
    l2 = Lot(lot_number="TRACE-L2", item_id=item_wip.id, quantity=50, initial_quantity=50, production_date=date.today())
    l3 = Lot(lot_number="TRACE-L3", item_id=item_wip.id, quantity=10, initial_quantity=10, production_date=date.today())
    db_session.add_all([l1, l2, l3])
    db_session.commit()
    
    # Link
    g1 = LotGenealogy(input_lot_id=l1.id, output_lot_id=l2.id, process_id=proc_shearing.id, quantity_consumed=50)
    g2 = LotGenealogy(input_lot_id=l2.id, output_lot_id=l3.id, process_id=proc_press.id, quantity_consumed=10)
    db_session.add_all([g1, g2])
    db_session.commit()
    
    # Trace Forward from L1
    response = client.get(f"/api/v1/trace/forward?lot_number=TRACE-L1")
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    produced = data["produced_lots"]
    assert len(produced) > 0 # Should find L2
    
    # Find L2
    l2_node = next((item for item in produced if item["lot_no"] == "TRACE-L2"), None)
    assert l2_node is not None
    
    # Find L3 (Recursive child) 
    l3_node = next((item for item in produced if item["lot_no"] == "TRACE-L3"), None)
    assert l3_node is not None
