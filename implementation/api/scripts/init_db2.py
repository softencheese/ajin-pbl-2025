import json
import os
import sys
from datetime import date, timedelta
import random

# Add the parent directory to sys.path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.process import Process
from app.models.item import Item
from app.models.rfid import RFIDReaderLocation
from app.models.lot import Lot
from app.models.pallet import Pallet

VIRT_DATA_PATH = os.path.join(os.path.dirname(__file__), "virt_data.json")
def load_virt_data():
    print(f"Loading virt_data from {VIRT_DATA_PATH}...")
    with open(VIRT_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)

def init_db():
    """virt_data.json 기반 DB 초기화"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    data = load_virt_data()
    try:
        create_processes(db, data)
        create_items(db, data)
        create_reader_locations(db, data)
        create_lots(db, data)
        create_pallets(db, data)
        print("\n✅ virt_data 기반 시딩 완료!")
        print_summary(db)
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_processes(db: Session, data):
    print("\n📦 Creating processes...")
    for p_data in data["processes"]:
        existing = db.query(Process).filter(Process.process_code == p_data["process_code"]).first()
        if not existing:
            process = Process(**p_data)
            db.add(process)
            print(f"  + {p_data['process_name']} ({p_data['production_line']})")
    db.commit()

def create_items(db: Session, data):
    print("\n📦 Creating items...")
    # RAW
    for i_data in data["raw_items"]:
        i_data = dict(i_data)
        i_data["item_type"] = "RAW"
        i_data.setdefault("unit", "KG")
        i_data.setdefault("spec", "")
        i_data.setdefault("vehicle_model", None)
        i_data.setdefault("default_supplier", "")
        existing = db.query(Item).filter(Item.item_code == i_data["item_code"]).first()
        if not existing:
            item = Item(**i_data)
            db.add(item)
            print(f"  + [RAW] {i_data['item_code']}")
    # WIP
    for w in data["wip_items"]:
        item_code = f"{w['code']}-{w['vehicle_model']}-SH"
        i_data = {
            "item_code": item_code,
            "item_name": w["item_name"],
            "item_type": "WIP",
            "unit": w.get("unit", "EA"),
            "vehicle_model": w["vehicle_model"],
            "spec": w.get("spec_suffix", ""),
        }
        existing = db.query(Item).filter(Item.item_code == i_data["item_code"]).first()
        if not existing:
            item = Item(**i_data)
            db.add(item)
            print(f"  + [WIP] {i_data['item_code']}")
    # PRODUCT
    for p in data["product_items"]:
        item_code = f"{p['code']}-{p['vehicle_model']}"
        i_data = {
            "item_code": item_code,
            "item_name": p["item_name"],
            "item_type": "PRODUCT",
            "unit": p.get("unit", "EA"),
            "vehicle_model": p["vehicle_model"],
            "spec": p.get("spec_suffix", ""),
        }
        existing = db.query(Item).filter(Item.item_code == i_data["item_code"]).first()
        if not existing:
            item = Item(**i_data)
            db.add(item)
            print(f"  + [PRODUCT] {i_data['item_code']}")
    db.commit()

def create_reader_locations(db: Session, data):
    print("\n📦 Creating reader locations...")
    # process_code -> id 매핑
    process_map = {p.process_code: p.id for p in db.query(Process).all()}
    for r in data["reader"]["reader-info"]:
        process_id = process_map.get(r.get("process-code"))
        for inner in r.get("inner", []):
            port_name = f"{r['prot-name']}-{inner['prefix-name']}"
            location_type = inner["prefix-name"] if inner["prefix-name"] in ["IN", "OUT", "HOLD", "DEFECT", "FINISH", "RETURN"] else None
            desc = inner.get("description", "")
            existing = db.query(RFIDReaderLocation).filter(RFIDReaderLocation.port_name == port_name).first()
            if not existing:
                location = RFIDReaderLocation(
                    port_name=port_name,
                    process_id=process_id,
                    location_type=location_type,
                    description=desc,
                    is_active=True
                )
                db.add(location)
                print(f"  + {port_name} -> {desc} ({location_type})")
    db.commit()

def create_lots(db: Session, data):
    print("\n📦 Creating lots...")
    today = date.today()
    
    # process_code -> id 매핑
    receiving_process = db.query(Process).filter(Process.process_code == "SHEARING").first()
    press_process = db.query(Process).filter(Process.process_code == "PRESS").first()
    assembly_process = db.query(Process).filter(Process.process_code == "ASSEMBLY").first()
    shipping_process = db.query(Process).filter(Process.process_code == "SHIPPING").first()
    
    # RAW LOT 3개 (최근 3일)
    for i, raw in enumerate(data["raw_items"]):
        item = db.query(Item).filter(Item.item_code == raw["item_code"]).first()
        for d in range(3):
            prod_date = today - timedelta(days=d)
            lot_number = f"L{prod_date.strftime('%y%m%d')}-{item.item_code[-5:]}-{str(i+1).zfill(3)}"
            existing = db.query(Lot).filter(Lot.lot_number == lot_number).first()
            if not existing:
                lot = Lot(
                    lot_number=lot_number,
                    barcode=f"BC{lot_number}",
                    item_id=item.id,
                    quantity=1000,
                    initial_quantity=1000,
                    status="STOCK",
                    production_date=prod_date,
                    supplier=item.default_supplier,
                    worker_name="입고담당",
                    qc_passed=True,
                    process_id=receiving_process.id if receiving_process else None
                )
                db.add(lot)
    # WIP LOT 1개
    for w in data["wip_items"]:
        item_code = f"{w['code']}-{w['vehicle_model']}-SH"
        item = db.query(Item).filter(Item.item_code == item_code).first()
        lot_number = f"W{today.strftime('%y%m%d')}-{item_code[:8]}-001"
        existing = db.query(Lot).filter(Lot.lot_number == lot_number).first()
        if not existing:
            lot = Lot(
                lot_number=lot_number,
                barcode=f"BC{lot_number}",
                item_id=item.id,
                quantity=100,
                initial_quantity=100,
                status="PROCESS",
                production_date=today,
                supplier=None,
                worker_name="가공담당",
                qc_passed=True,
                process_id=press_process.id if press_process else None
            )
            db.add(lot)
    # PRODUCT LOT 1개
    for p in data["product_items"]:
        item_code = f"{p['code']}-{p['vehicle_model']}"
        item = db.query(Item).filter(Item.item_code == item_code).first()
        lot_number = f"P{today.strftime('%y%m%d')}-{item_code[-6:]}-001"
        existing = db.query(Lot).filter(Lot.lot_number == lot_number).first()
        if not existing:
            lot = Lot(
                lot_number=lot_number,
                barcode=f"BC{lot_number}",
                item_id=item.id,
                quantity=50,
                initial_quantity=50,
                status="STOCK",
                production_date=today,
                supplier=None,
                worker_name="조립담당",
                qc_passed=True,
                process_id=assembly_process.id if assembly_process else None
            )
            db.add(lot)
    db.commit()

# def create_lot_ggenealogyries(db: Session, data):


def create_pallets(db: Session, data):
    print("\n📦 Creating pallets...")
    # pallette-data: 4x3
    lots = db.query(Lot).all()
    lot_ids = [l.id for l in lots]
    idx = 0

    pallet_no = f"PLT-{str(idx+1).zfill(5)}"
    existing = db.query(Pallet).filter(Pallet.pallet_no == pallet_no).first()
    status = "Empty"
    if not existing:
        pallet = Pallet(
            pallet_no=pallet_no,
            rfid_epc="E280116020005000",
            lot_id=None,
            status=status,
            tag_status="AVAILABLE",
            current_process_id=None,
            quantity= 100 if status != "Stock" else 0
        )
        db.add(pallet)
    idx += 1

    for row in data["pallette-data"]:
        for epc, status in row:
            pallet_no = f"PLT-{str(idx+1).zfill(5)}"
            existing = db.query(Pallet).filter(Pallet.pallet_no == pallet_no).first()
            lot_id = lot_ids[idx % len(lot_ids)] if lot_ids else None
            if not existing:
                pallet = Pallet(
                    pallet_no=pallet_no,
                    rfid_epc=epc.replace(" ", ""),
                    lot_id=lot_id,
                    status=status,
                    tag_status="AVAILABLE",
                    current_process_id=None,
                    quantity= 100 if status != "Stock" else 0
                )
                db.add(pallet)
            idx += 1
    db.commit()

def print_summary(db: Session):
    print("\n" + "="*50)
    print("📊 데이터 요약")
    print("="*50)
    process_count = db.query(Process).count()
    item_count = db.query(Item).count()
    raw_count = db.query(Item).filter(Item.item_type == "RAW").count()
    wip_count = db.query(Item).filter(Item.item_type == "WIP").count()
    product_count = db.query(Item).filter(Item.item_type == "PRODUCT").count()
    reader_count = db.query(RFIDReaderLocation).count()
    lot_count = db.query(Lot).count()
    pallet_count = db.query(Pallet).count()
    print(f"  공정 (Process): {process_count}개")
    print(f"  품목 (Item): {item_count}개")
    print(f"    - 원자재 (RAW): {raw_count}개")
    print(f"    - 재공품 (WIP): {wip_count}개")
    print(f"    - 완제품 (PRODUCT): {product_count}개")
    print(f"  리더기 위치: {reader_count}개")
    print(f"  LOT: {lot_count}개")
    print(f"  팔레트: {pallet_count}개")
    print("="*50)

if __name__ == "__main__":
    init_db()
