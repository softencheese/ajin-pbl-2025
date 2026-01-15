from datetime import datetime, date
import time
from fastapi.testclient import TestClient
from app.models.process import Process
from app.models.item import Item
from app.models.rfid import RFIDReaderLocation
from app.models.lot import Lot
from app.models.pallet import Pallet

def test_full_system_flow(client: TestClient, db_session):
    """
    [E2E Scenario]
    1. 원자재(RAW) 입고 -> Lot 생성
    2. 샤링(SHEARING) 공정
       - 생산 Lot 생성 및 팔레트(PLT-SH) 매핑
       - SHEARING-OUT 리더기 스캔 -> 재고(Stock) 상태
    3. 프레스(PRESS) 공정
       - PRESS-IN 스캔 -> 투입(Consuming) -> 공 팔레트(Empty)
       - 생산 Lot 생성 및 팔레트(PLT-PR) 매핑
       - PRESS-OUT 스캔 -> 재고(Stock)
    4. 조립(ASSEMBLY) 공정
       - ASSEMBLY-IN 스캔 -> 투입(Consuming)
    """

    # 0. 데이터 준비 (init_db 데이터 사용)
    # 필요한 마스터 데이터 조회
    raw_item = db_session.query(Item).filter(Item.item_code == "COIL-SPCC-16").first()
    wip_sh_item = db_session.query(Item).filter(Item.item_code.like("%-SH")).first() # 샤링품
    wip_pr_item = db_session.query(Item).filter(Item.item_code.like("%-PR")).first() # 프레스품
    
    assert raw_item
    assert wip_sh_item
    assert wip_pr_item
    
    proc_shearing = db_session.query(Process).filter(Process.process_code == "SHEARING").first()
    proc_press = db_session.query(Process).filter(Process.process_code == "PRESS").first()
    proc_assembly = db_session.query(Process).filter(Process.process_code == "ASSEMBLY").first()
    
    assert proc_shearing
    assert proc_press
    assert proc_assembly
    
    # 1. 원자재 입고 (Receiving Lot)
    # POST /api/v1/lots/receiving
    res = client.post("/api/v1/lots/receiving", json={
        "item_id": raw_item.id,
        "quantity": 1000,
        "production_date": date.today().isoformat(),
        "supplier": "Test Supplier",
        "notes": "E2E Test Raw Material"
    })
    assert res.status_code == 201
    raw_lot_data = res.json()
    raw_lot_id = raw_lot_data["id"]
    print(f"\n[Step 1] Raw Lot Created: {raw_lot_data['lot_number']}")

    # 2. 샤링 공정 (Shearing)
    # 2-1. 생산 Lot 생성 (Manual)
    # POST /api/v1/lots
    res = client.post("/api/v1/lots", json={
        "item_id": wip_sh_item.id,
        "process_id": proc_shearing.id,
        "quantity": 200,
        "production_date": date.today().isoformat(),
        "worker_name": "Shear Worker",
        "input_lots": [{"lot_id": raw_lot_id, "quantity_consumed": 100}]
    })
    assert res.status_code == 201
    shear_lot_data = res.json()
    shear_lot_id = shear_lot_data["id"]
    print(f"[Step 2] Shearing Lot Created: {shear_lot_data['lot_number']}")
    
    # 2-2. 팔레트 생성 및 매핑
    epc_shear = "EPC-SHEAR-TEST"
    plt_shear = "PLT-SHEAR-TEST"
    res = client.post("/api/v1/pallets", json={"pallet_no": plt_shear, "rfid_epc": epc_shear, "status": "Empty"})
    assert res.status_code == 201
    pallet_sh_id = res.json()["id"]
    
    # 매핑
    res = client.put(f"/api/v1/pallets/{pallet_sh_id}/link-lot", json={"lot_id": shear_lot_id})
    assert res.status_code == 200
    
    # 2-3. SHEARING-OUT 스캔 (-> Stock)
    # "SHEARING-OUT" 포트명은 init_db에 있음
    scan_payload = {
        "epc": epc_shear,
        "port_name": "SHEARING-OUT",
        "scan_time": datetime.now().isoformat()
    }
    res = client.post("/api/v1/rfid/scan", json=scan_payload)
    assert res.status_code == 200
    scan_data = res.json()
    assert scan_data["success"] is True
    assert scan_data["pallet"]["current_status"] == "Stock"
    print(f"[Step 2] Shearing OUT Scan OK -> Status: {scan_data['pallet']['current_status']}")

    # 3. 프레스 공정 (Press)
    # 3-1. PRESS-IN 스캔 (-> Consuming)
    scan_payload = {
        "epc": epc_shear,
        "port_name": "PRESS-IN",
        "scan_time": datetime.now().isoformat()
    }
    res = client.post("/api/v1/rfid/scan", json=scan_payload)
    assert res.status_code == 200
    scan_data = res.json()
    assert scan_data["success"] is True
    assert scan_data["pallet"]["current_status"] == "Consuming"
    print(f"[Step 3] Press IN Scan OK -> Status: {scan_data['pallet']['current_status']}")
    
    # 한번 더 스캔하면 -> Empty (다 썼음)
    time.sleep(0.1)
    scan_payload["scan_time"] = datetime.now().isoformat()
    res = client.post("/api/v1/rfid/scan", json=scan_payload)
    assert res.status_code == 200
    # 여기서는 Pallet가 리턴되지 않을 수 있음 (Empty 상태, Lot 연결 해제됨)
    # 응답 구조 확인 필요. 보통 success=True, pallet=None or pallet=...
    scan_data = res.json()
    assert scan_data["success"] is True
    # 모델 로직에 따라 팔레트가 Empty로 바뀌고, lot_id가 null이 됨.
    
    # 3-2. 생산 Lot 생성 (Press Output)
    res = client.post("/api/v1/lots", json={
        "item_id": wip_pr_item.id,
        "process_id": proc_press.id,
        "quantity": 150,
        "production_date": date.today().isoformat(),
        "worker_name": "Press Worker"
    })
    assert res.status_code == 201
    press_lot_id = res.json()["id"]
    
    # 3-3. 팔레트 생성 (Press Output Pallet)
    epc_press = "EPC-PRESS-TEST"
    plt_press = "PLT-PRESS-TEST"
    res = client.post("/api/v1/pallets", json={"pallet_no": plt_press, "rfid_epc": epc_press, "status": "Empty"})
    assert res.status_code == 201
    pallet_pr_id = res.json()["id"]
    
    # 매핑
    client.put(f"/api/v1/pallets/{pallet_pr_id}/link-lot", json={"lot_id": press_lot_id})
    
    # 3-4. PRESS-OUT 스캔 (-> Stock)
    res = client.post("/api/v1/rfid/scan", json={
        "epc": epc_press, 
        "port_name": "PRESS-OUT", 
        "scan_time": datetime.now().isoformat()
    })
    assert res.status_code == 200
    assert res.json()["pallet"]["current_status"] == "Stock"
    print(f"[Step 3] Press OUT Scan OK -> Status: Stock")
    
    # 4. 조립 공정 (Assembly)
    # 4-1. ASSEMBLY-IN 스캔 (-> Consuming)
    res = client.post("/api/v1/rfid/scan", json={
        "epc": epc_press, 
        "port_name": "ASSEMBLY-IN", 
        "scan_time": datetime.now().isoformat()
    })
    assert res.status_code == 200
    assert res.json()["pallet"]["current_status"] == "Consuming"
    print(f"[Step 4] Assembly IN Scan OK -> Status: Consuming")
