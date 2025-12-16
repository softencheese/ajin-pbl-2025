from datetime import datetime, date
from app.models.process import Process
from app.models.item import Item
from app.models.rfid import RFIDReaderLocation
from app.models.pallet import Pallet
from app.models.lot import Lot
from app.models.lot_genealogy import LotGenealogy

def setup_test_data(db):
    """테스트용 기초 데이터 생성"""
    # 1. Process
    p1 = Process(process_code="SHEARING", process_name="샤링", process_order=1, production_line="400T")
    p2 = Process(process_code="PRESS", process_name="프레스", process_order=2, production_line="1500T")
    db.add_all([p1, p2])
    db.commit()
    
    # 2. Item
    i1 = Item(item_code="RAW-001", item_name="Steel Coil", item_type="RAW")
    i2 = Item(item_code="WIP-001", item_name="Panel Part", item_type="WIP")
    db.add_all([i1, i2])
    db.commit()
    
    # 3. Reader Location (Press IN)
    r1 = RFIDReaderLocation(
        port_name="COM3",
        process_id=p2.id,
        location_type="IN",
        description="Press Input"
    )
    db.add(r1)
    db.commit()
    
    return p1, p2, i1, i2

def test_wrong_part_validation(client, db_session):
    """오투입 검증 테스트"""
    p1, p2, i1, i2 = setup_test_data(db_session)
    
    # LOT & Pallet 생성 (RAW Item)
    lot_raw = Lot(
        lot_number="LOT-RAW-001",
        item_id=i1.id, # RAW type
        quantity=100,
        initial_quantity=100,
        production_date=date.today()
    )
    db_session.add(lot_raw)
    db_session.commit()
    
    pallet_raw = Pallet(
        pallet_no="PLT-001",
        rfid_epc="EPC-RAW-001",
        status="Stock",
        lot_id=lot_raw.id
    )
    db_session.add(pallet_raw)
    db_session.commit()
    
    # FAIL Case: Scan RAW at Press (Requires WIP)
    response = client.post("/api/v1/rfid/scan", json={
        "epc": "EPC-RAW-001",
        "port_name": "COM3", # Press IN
        "scan_time": datetime.now().isoformat()
    })
    
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "WRONG_PART"
    
    # Success Case: Scan WIP at Press
    lot_wip = Lot(
        lot_number="LOT-WIP-001",
        item_id=i2.id, # WIP type
        quantity=100,
        initial_quantity=100,
        production_date=date.today()
    )
    db_session.add(lot_wip)
    db_session.commit()
    
    pallet_wip = Pallet(
        pallet_no="PLT-002",
        rfid_epc="EPC-WIP-001",
        status="Stock",
        lot_id=lot_wip.id
    )
    db_session.add(pallet_wip)
    db_session.commit()
    
    response = client.post("/api/v1/rfid/scan", json={
        "epc": "EPC-WIP-001",
        "port_name": "COM3", # Press IN
        "scan_time": datetime.now().isoformat()
    })
    
    data = response.json()
    assert data["success"] is True

def test_recursive_trace(client, db_session):
    """재귀적 추적 테스트"""
    p1, p2, i1, i2 = setup_test_data(db_session)
    
    # Create Genealogy: L1(RAW) -> L2(WIP) -> L3(WIP-2)
    l1 = Lot(lot_number="L1", item_id=i1.id, quantity=100, initial_quantity=100, production_date=date.today())
    l2 = Lot(lot_number="L2", item_id=i2.id, quantity=50, initial_quantity=50, production_date=date.today())
    l3 = Lot(lot_number="L3", item_id=i2.id, quantity=10, initial_quantity=10, production_date=date.today())
    db_session.add_all([l1, l2, l3])
    db_session.commit()
    
    g1 = LotGenealogy(input_lot_id=l1.id, output_lot_id=l2.id, process_id=p1.id, quantity_consumed=50)
    g2 = LotGenealogy(input_lot_id=l2.id, output_lot_id=l3.id, process_id=p2.id, quantity_consumed=10)
    db_session.add_all([g1, g2])
    db_session.commit()
    
    # Trace Forward from L1
    # Should find L2 AND L3 (Recursive)
    # Note: We need to test the service method directly or via API endpoint if available.
    # The API endpoint is GET /trace/forward
    
    response = client.get(f"/api/v1/trace/forward?lot_number=L1")
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    produced = data["produced_lots"]
    assert len(produced) > 0 # Should find L2
    
    # Find L2 in produced_lots
    l2_node = next((item for item in produced if item["lot_no"] == "L2"), None)
    assert l2_node is not None
    
    # Find L3 in L2's child_lots or recursive structure
    # My implementation puts L3 as keys in the flat produced_lots_map, but let's check the API response structure.
    # Wait, ForwardTraceResponse returns a LIST of ProducedLot. 
    # My recursive logic adds ALL descendants to this list.
    
    l3_node = next((item for item in produced if item["lot_no"] == "L3"), None)
    assert l3_node is not None
