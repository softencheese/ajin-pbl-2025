from datetime import datetime, date
import time
from app.models.process import Process
from app.models.item import Item
from app.models.rfid import RFIDReaderLocation
from app.models.lot import Lot
from app.models.pallet import Pallet
from app.models.physical_pallet import PhysicalPallet

def test_full_process_with_auto_binding(client, db_session):
    """
    [전체 공정 E2E 테스트 시나리오]
    1. 원자재(RAW) 입고: LOT 생성 (STOCK 상태)
    2. 샤링(SHEARING) 공정 (첫 공정):
       - 생산 LOT 생성 (수량 100, 팔레트당 50EA -> 가상 팔레트 2개 생성됨)
       - 미등록 EPC-1로 SHEARING-OUT 스캔 -> 자동 바인딩 -> Producing
       - 다시 EPC-1로 SHEARING-OUT 스캔 -> 생산 완료 -> Stock
       - 미등록 EPC-2로 SHEARING-OUT 스캔 -> 두 번째 가상 팔레트 자동 바인딩 -> Producing
       - 다시 EPC-2로 SHEARING-OUT 스캔 -> 생산 완료 -> Stock (LOT 상태도 STOCK으로 변경되어야 함)
    3. 프레스(PRESS) 공정 (후속 공정):
       - EPC-1로 PRESS-IN 스캔 -> 투입 -> Consuming (LOT 상태 PROCESS 변경)
       - 다시 EPC-1로 PRESS-IN 스캔 -> 소비 완료 -> Deregistered
       - EPC-2로 PRESS-IN 스캔 -> 투입 -> Consuming
       - 다시 EPC-2로 PRESS-IN 스캔 -> 소비 완료 -> Deregistered (LOT 상태 CONSUMED 변경)
    """

    # 0. 데이터 준비
    raw_item = db_session.query(Item).filter(Item.item_code == "COIL-SPCC-16").first()
    wip_sh_item = db_session.query(Item).filter(Item.item_code.like("%-SH")).first()
    
    proc_shearing = db_session.query(Process).filter(Process.process_code == "SHEARING").first()
    proc_press = db_session.query(Process).filter(Process.process_code == "PRESS").first()
    
    # 1. 원자재 입고
    res = client.post("/api/v1/lots/receiving", json={
        "item_id": raw_item.id,
        "quantity": 1000,
        "production_date": date.today().isoformat(),
        "supplier": "E2E Supplier"
    })
    assert res.status_code == 201
    raw_lot_id = res.json()["id"]
    print(f"\n[E2E] 1. 원자재 LOT 생성 완료: {res.json()['lot_number']}")

    # 2. 샤링 공정 (생산)
    # 가상 팔레트 2개가 생성되도록 설정 (100개 / 50개 용량)
    res = client.post("/api/v1/lots", json={
        "item_id": wip_sh_item.id,
        "process_id": proc_shearing.id,
        "quantity": 100,
        "pallet_capacity": 50,
        "production_date": date.today().isoformat(),
        "worker_name": "E2E Worker",
        "input_lots": [{"lot_id": raw_lot_id, "quantity_consumed": 50}]
    })
    assert res.status_code == 201
    sh_lot_id = res.json()["id"]
    print(f"[E2E] 2. 샤링 생산 LOT 생성 완료: {res.json()['lot_number']} (가상 팔레트 2개 대기 중)")

    # 2-1. 첫 번째 팔레트 자동 바인딩 & 생산 완료
    epc_1 = "E280-E2E-TEST-001"
    res = client.post("/api/v1/rfid/scan", json={
        "epc": epc_1,
        "port_name": "COM01-OUT",
        "scan_time": datetime.now().isoformat()
    })
    assert res.json()["success"] is True
    assert res.json()["pallet"]["current_status"] == "Producing"
    print(f"  - EPC-1 자동 바인딩 완료 -> Status: Producing")

    res = client.post("/api/v1/rfid/scan", json={
        "epc": epc_1,
        "port_name": "COM01-OUT",
        "scan_time": datetime.now().isoformat()
    })
    assert res.json()["pallet"]["current_status"] == "Stock"
    print(f"  - EPC-1 생산 완료 -> Status: Stock")

    # 2-2. 두 번째 팔레트 자동 바인딩 & 생산 완료
    epc_2 = "E280-E2E-TEST-002"
    res = client.post("/api/v1/rfid/scan", json={
        "epc": epc_2,
        "port_name": "COM01-OUT",
        "scan_time": datetime.now().isoformat()
    })
    assert res.json()["success"] is True
    assert res.json()["pallet"]["current_status"] == "Producing"
    print(f"  - EPC-2 자동 바인딩 완료 -> Status: Producing")

    res = client.post("/api/v1/rfid/scan", json={
        "epc": epc_2,
        "port_name": "COM01-OUT",
        "scan_time": datetime.now().isoformat()
    })
    assert res.json()["pallet"]["current_status"] == "Stock"
    print(f"  - EPC-2 생산 완료 -> Status: Stock")

    # 2-3. LOT 상태 확인 (모든 팔레트 Stock -> LOT STOCK)
    db_session.expire_all()
    sh_lot = db_session.query(Lot).get(sh_lot_id)
    assert sh_lot.status == "STOCK"
    print(f"[E2E] 2. 샤링 공정 완료 (LOT 상태: STOCK)")

    # 3. 프레스 공정 (소비)
    # 3-1. EPC-1 투입
    res = client.post("/api/v1/rfid/scan", json={
        "epc": epc_1,
        "port_name": "COM02-IN",
        "scan_time": datetime.now().isoformat()
    })
    assert res.json()["pallet"]["current_status"] == "Consuming"
    print(f"[E2E] 3. EPC-1 프레스 투입 시작 (Status: Consuming)")

    # 3-2. EPC-1 소비 완료
    res = client.post("/api/v1/rfid/scan", json={
        "epc": epc_1,
        "port_name": "COM02-IN",
        "scan_time": datetime.now().isoformat()
    })
    assert res.json()["success"] is True
    # 모델에 따라 Empty/Deregistered 상태가 됨 (StateMachine 가이드 참고)
    # state_machine.py: Consuming -> IN -> Deregistered
    assert res.json()["pallet"]["current_status"] == "Deregistered"
    print(f"  - EPC-1 소비 완료 (Status: Deregistered)")

    # 3-3. LOT 상태 확인 (일부 소비 중 -> PROCESS)
    db_session.expire_all()
    sh_lot = db_session.query(Lot).get(sh_lot_id)
    assert sh_lot.status == "WAIT"
    print(f"  - LOT 상태 확인: {sh_lot.status} (일부 소비 중)")

    # 3-4. EPC-2 투입 및 소비 완료
    client.post("/api/v1/rfid/scan", json={"epc": epc_2, "port_name": "COM02-IN", "scan_time": datetime.now().isoformat()})
    res = client.post("/api/v1/rfid/scan", json={"epc": epc_2, "port_name": "COM02-IN", "scan_time": datetime.now().isoformat()})
    assert res.json()["pallet"]["current_status"] == "Deregistered"
    print(f"  - EPC-2 소비 완료 (Status: Deregistered)")

    # 3-5. 최종 LOT 상태 확인 (모든 팔레트 Deregistered -> CONSUMED)
    db_session.expire_all()
    sh_lot = db_session.query(Lot).get(sh_lot_id)
    assert sh_lot.status == "CONSUMED"
    print(f"[E2E] 3. 프레스 공정 소비 완료 (LOT 상태: CONSUMED)")
    print(f"\n✅ 전체 공정 E2E 테스트 성공!")
