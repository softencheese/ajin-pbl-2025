import sys
import os
from datetime import date, datetime, timedelta
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


def init_db():
    """메인 초기화 함수"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        create_processes(db)
        create_items(db)
        create_reader_locations(db)
        create_lots(db)
        create_pallets(db)
        print("\n✅ 테스트 데이터 시딩 완료!")
        print_summary(db)
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_processes(db: Session):
    """공정 마스터 데이터 생성 (5개)"""
    print("\n📦 Creating processes...")
    processes = [
        {"process_code": "RECEIVING", "process_name": "입고", "process_order": 0, "production_line": "입고장", "allowed_item_types": "RAW"},
        {"process_code": "SHEARING", "process_name": "샤링", "process_order": 1, "production_line": "400T", "allowed_item_types": "RAW", "is_first_process": True},
        {"process_code": "PRESS", "process_name": "프레스", "process_order": 2, "production_line": "1500T", "allowed_item_types": "WIP"},
        {"process_code": "ASSEMBLY", "process_name": "조립", "process_order": 3, "production_line": "조립라인", "allowed_item_types": "WIP,PRODUCT"},
        {"process_code": "SHIPPING", "process_name": "출하", "process_order": 4, "production_line": "출하장", "allowed_item_types": "PRODUCT"},
    ]

    for p_data in processes:
        existing = db.query(Process).filter(Process.process_code == p_data["process_code"]).first()
        if not existing:
            process = Process(**p_data)
            db.add(process)
            print(f"  + {p_data['process_name']} ({p_data['production_line']})")
    db.commit()


def create_items(db: Session):
    """품목 마스터 데이터 생성"""
    print("\n📦 Creating items...")
    
    # 원자재 (RAW) - 코일/시트 형태, 10개
    raw_items = [
        {"item_code": "COIL-SPCC-16", "item_name": "SPCC 냉연강판 1.6T", "item_type": "RAW", "unit": "KG", "spec": "1.6T, 1219mm", "default_supplier": "포스코"},
        {"item_code": "COIL-SPCC-20", "item_name": "SPCC 냉연강판 2.0T", "item_type": "RAW", "unit": "KG", "spec": "2.0T, 1219mm", "default_supplier": "현대제철"},
        {"item_code": "COIL-SPHC-18", "item_name": "SPHC 열연강판 1.8T", "item_type": "RAW", "unit": "KG", "spec": "1.8T, 1219mm", "default_supplier": "포스코"},
        {"item_code": "COIL-SPHC-23", "item_name": "SPHC 열연강판 2.3T", "item_type": "RAW", "unit": "KG", "spec": "2.3T, 1219mm", "default_supplier": "현대제철"},
        {"item_code": "COIL-GA-12", "item_name": "GA 아연도금강판 1.2T", "item_type": "RAW", "unit": "KG", "spec": "1.2T, 1219mm", "default_supplier": "포스코"},
        {"item_code": "COIL-GA-16", "item_name": "GA 아연도금강판 1.6T", "item_type": "RAW", "unit": "KG", "spec": "1.6T, 1219mm", "default_supplier": "현대제철"},
        {"item_code": "COIL-STS-10", "item_name": "STS304 스테인리스 1.0T", "item_type": "RAW", "unit": "KG", "spec": "1.0T, 1219mm", "default_supplier": "포스코"},
        {"item_code": "COIL-STS-15", "item_name": "STS430 스테인리스 1.5T", "item_type": "RAW", "unit": "KG", "spec": "1.5T, 1219mm", "default_supplier": "현대제철"},
    ]
    
    # 차종 목록
    vehicles = ["JX1", "NE", "K9", "GN7", "EV9"]
    
    # 재공품 (WIP) - 샤링/프레스 결과물, 15개
    wip_items = []
    wip_parts = [
        ("71412", "PNL-FR DR INR LH", "LH"),
        ("71413", "PNL-FR DR INR RH", "RH"),
        ("71420", "PNL-FR DR OTR LH", "LH"),
        ("71421", "PNL-FR DR OTR RH", "RH"),
        ("71430", "REINF-FR DR LH", "LH"),
        ("71431", "REINF-FR DR RH", "RH"),
        ("76211", "PNL-RR DR INR LH", "LH"),
        ("76212", "PNL-RR DR INR RH", "RH"),
        ("77211", "PNL-TAILGATE INR", ""),
        ("77212", "PNL-TAILGATE OTR", ""),
    ]
    
    for code, name, spec_suffix in wip_parts:
        vehicle = random.choice(vehicles[:3])  # JX1, NE, K9 중 선택
        for suffix, stage in [("-SH", "샤링"), ("-PR", "프레스")]:
            wip_items.append({
                "item_code": f"{code}-{vehicle}{suffix}",
                "item_name": f"{name} ({stage})",
                "item_type": "WIP",
                "unit": "EA",
                "vehicle_model": vehicle,
                "spec": f"{spec_suffix}, {stage}완료" if spec_suffix else f"{stage}완료"
            })
    
    # 완제품 (PRODUCT) - 조립 완료품, 15개
    product_items = []
    product_parts = [
        ("ASSY-76211", "ASSY-FR DR MODULE LH", "LH"),
        ("ASSY-76212", "ASSY-FR DR MODULE RH", "RH"),
        ("ASSY-77211", "ASSY-RR DR MODULE LH", "LH"),
        ("ASSY-77212", "ASSY-RR DR MODULE RH", "RH"),
        ("ASSY-77300", "ASSY-TAILGATE MODULE", ""),
        ("ASSY-67110", "ASSY-HOOD MODULE", ""),
        ("ASSY-76801", "ASSY-SIDE SILL LH", "LH"),
        ("ASSY-76802", "ASSY-SIDE SILL RH", "RH"),
        ("ASSY-64710", "ASSY-CROSS MBR FR", ""),
        ("ASSY-64720", "ASSY-CROSS MBR RR", ""),
    ]
    
    for code, name, spec in product_parts:
        for vehicle in vehicles[:3]:  # JX1, NE, K9
            product_items.append({
                "item_code": f"{code}-{vehicle}",
                "item_name": f"{name}",
                "item_type": "PRODUCT",
                "unit": "EA",
                "vehicle_model": vehicle,
                "spec": f"{spec}, 완제품" if spec else "완제품"
            })

    all_items = raw_items + wip_items[:15] + product_items[:15]
    
    for i_data in all_items:
        existing = db.query(Item).filter(Item.item_code == i_data["item_code"]).first()
        if not existing:
            item = Item(**i_data)
            db.add(item)
            print(f"  + [{i_data['item_type']}] {i_data['item_code']}")
    db.commit()


def create_reader_locations(db: Session):
    """
    RFID 리더기 위치 마스터 데이터 생성
    - 입고: 리더기 없음
    - 샤링: OUT만 1개
    - 프레스: IN/OUT 각 1개
    - 조립: IN/OUT 각 1개
    - 출하: IN/OUT 각 1개
    """
    print("\n📦 Creating reader locations...")
    
    # 공정 조회
    shearing = db.query(Process).filter(Process.process_code == "SHEARING").first()
    press = db.query(Process).filter(Process.process_code == "PRESS").first()
    assembly = db.query(Process).filter(Process.process_code == "ASSEMBLY").first()
    shipping = db.query(Process).filter(Process.process_code == "SHIPPING").first()
    
    locations = [
        # 샤링: OUT만
        {"port_name": "SHEARING-OUT", "process_id": shearing.id if shearing else None, "location_type": "OUT", "description": "샤링 400T 배출"},
        # 프레스: IN/OUT
        {"port_name": "PRESS-IN", "process_id": press.id if press else None, "location_type": "IN", "description": "프레스 1500T 투입"},
        {"port_name": "PRESS-OUT", "process_id": press.id if press else None, "location_type": "OUT", "description": "프레스 1500T 배출"},
        # 조립: IN/OUT
        {"port_name": "ASSEMBLY-IN", "process_id": assembly.id if assembly else None, "location_type": "IN", "description": "조립라인 투입"},
        {"port_name": "ASSEMBLY-OUT", "process_id": assembly.id if assembly else None, "location_type": "OUT", "description": "조립라인 배출"},
        # 출하: IN/OUT
        {"port_name": "SHIPPING-IN", "process_id": shipping.id if shipping else None, "location_type": "IN", "description": "출하장 투입"},
        {"port_name": "SHIPPING-OUT", "process_id": shipping.id if shipping else None, "location_type": "FINISH", "description": "출하장 완료"},
        # 휴대용 리더기: 재고 확인용 (FIFO 검증, 재고 조회)
        {"port_name": "HANDHELD-01", "process_id": None, "location_type": None, "description": "휴대용 재고 확인 리더기"},
    ]

    for l_data in locations:
        existing = db.query(RFIDReaderLocation).filter(RFIDReaderLocation.port_name == l_data["port_name"]).first()
        if not existing:
            location = RFIDReaderLocation(**l_data)
            db.add(location)
            print(f"  + {l_data['port_name']} -> {l_data['description']} ({l_data['location_type']})")
    db.commit()


def create_lots(db: Session):
    """LOT 샘플 데이터 생성 (~100개)"""
    print("\n📦 Creating lots...")
    
    # 품목 조회
    items = db.query(Item).all()
    raw_items = [i for i in items if i.item_type == "RAW"]
    wip_items = [i for i in items if i.item_type == "WIP"]
    product_items = [i for i in items if i.item_type == "PRODUCT"]
    
    # 공정 조회
    shearing = db.query(Process).filter(Process.process_code == "SHEARING").first()
    press = db.query(Process).filter(Process.process_code == "PRESS").first()
    assembly = db.query(Process).filter(Process.process_code == "ASSEMBLY").first()
    
    today = date.today()
    lot_count = 0
    statuses_raw = ["WAIT", "STOCK", "CONSUMED"]
    statuses_wip = ["PROCESS", "STOCK"]
    statuses_product = ["STOCK", "SHIPPED"]
    
    # 원자재 LOT (40개) - 최근 14일치
    for day_offset in range(14):
        prod_date = today - timedelta(days=day_offset)
        for raw_item in raw_items:
            if lot_count >= 40:
                break
            lot_number = f"L{prod_date.strftime('%y%m%d')}-{raw_item.item_code[-5:]}-{str(lot_count+1).zfill(3)}"
            existing = db.query(Lot).filter(Lot.lot_number == lot_number).first()
            if not existing:
                qty = random.randint(500, 2000)
                status = random.choice(statuses_raw) if day_offset > 3 else "WAIT"
                lot = Lot(
                    lot_number=lot_number,
                    barcode=f"BC{lot_number}",
                    item_id=raw_item.id,
                    quantity=qty if status != "CONSUMED" else 0,
                    initial_quantity=qty,
                    status=status,
                    production_date=prod_date,
                    supplier=raw_item.default_supplier,
                    worker_name="입고담당",
                    qc_passed=True if status != "WAIT" else False,
                )
                db.add(lot)
                lot_count += 1
    
    # WIP LOT (35개) - 최근 10일치
    wip_lot_count = 0
    for day_offset in range(10):
        prod_date = today - timedelta(days=day_offset)
        for wip_item in wip_items:
            if wip_lot_count >= 35:
                break
            lot_number = f"W{prod_date.strftime('%y%m%d')}-{wip_item.item_code[:8]}-{str(wip_lot_count+1).zfill(3)}"
            existing = db.query(Lot).filter(Lot.lot_number == lot_number).first()
            if not existing:
                qty = random.randint(30, 150)
                is_shearing = "-SH" in wip_item.item_code
                process = shearing if is_shearing else press
                status = random.choice(statuses_wip)
                lot = Lot(
                    lot_number=lot_number,
                    barcode=f"BC{lot_number}",
                    item_id=wip_item.id,
                    quantity=qty,
                    initial_quantity=qty,
                    status=status,
                    production_date=prod_date,
                    process_id=process.id if process else None,
                    worker_name="생산담당",
                    qc_passed=day_offset > 0,
                )
                db.add(lot)
                wip_lot_count += 1
                lot_count += 1
    
    # 완제품 LOT (25개) - 최근 7일치
    product_lot_count = 0
    for day_offset in range(7):
        prod_date = today - timedelta(days=day_offset)
        for product_item in product_items:
            if product_lot_count >= 25:
                break
            lot_number = f"P{prod_date.strftime('%y%m%d')}-{product_item.item_code[-6:]}-{str(product_lot_count+1).zfill(3)}"
            existing = db.query(Lot).filter(Lot.lot_number == lot_number).first()
            if not existing:
                qty = random.randint(10, 50)
                status = random.choice(statuses_product)
                lot = Lot(
                    lot_number=lot_number,
                    barcode=f"BC{lot_number}",
                    item_id=product_item.id,
                    quantity=qty if status != "SHIPPED" else 0,
                    initial_quantity=qty,
                    status=status,
                    production_date=prod_date,
                    process_id=assembly.id if assembly else None,
                    worker_name="조립담당",
                    qc_passed=True,
                )
                db.add(lot)
                product_lot_count += 1
                lot_count += 1
    
    db.commit()
    print(f"  + {lot_count} LOTs created (RAW: 40, WIP: 35, PRODUCT: 25)")


def create_pallets(db: Session):
    """팔레트 샘플 데이터 생성 (LOT당 10~20개)"""
    print("\n📦 Creating pallets...")
    
    # STOCK/PROCESS 상태의 LOT만 대상
    lots = db.query(Lot).filter(Lot.status.in_(["STOCK", "PROCESS", "WAIT"])).all()
    
    pallet_count = 0
    pallet_idx = 1
    
    for lot in lots:
        # LOT당 10~20개 팔레트 생성
        num_pallets = random.randint(10, 20)
        qty_per_pallet = max(1, lot.quantity // num_pallets) if lot.quantity > 0 else 0
        
        for i in range(num_pallets):
            pallet_no = f"PLT-{str(pallet_idx).zfill(5)}"
            rfid_epc = f"E280116020005{str(pallet_idx).zfill(7)}"
            
            existing = db.query(Pallet).filter(Pallet.pallet_no == pallet_no).first()
            if not existing:
                # LOT 상태에 따른 팔레트 상태 결정
                if lot.status == "STOCK":
                    status = "Stock"
                elif lot.status == "PROCESS":
                    status = "Producing"
                elif lot.status == "WAIT":
                    status = "Empty"
                else:
                    status = "Empty"
                
                pallet = Pallet(
                    pallet_no=pallet_no,
                    rfid_epc=rfid_epc,
                    lot_id=lot.id if status != "Empty" else None,
                    status=status,
                    tag_status="IN_USE" if status != "Empty" else "AVAILABLE",
                    current_process_id=lot.process_id,
                    quantity=qty_per_pallet if status != "Empty" else 0,
                )
                db.add(pallet)
                pallet_count += 1
                pallet_idx += 1
    
    # 추가 빈 팔레트 20개
    for i in range(20):
        pallet_no = f"PLT-E{str(i+1).zfill(4)}"
        rfid_epc = f"E280116020009{str(i+1).zfill(7)}"
        
        existing = db.query(Pallet).filter(Pallet.pallet_no == pallet_no).first()
        if not existing:
            pallet = Pallet(
                pallet_no=pallet_no,
                rfid_epc=rfid_epc,
                lot_id=None,
                status="Empty",
                tag_status="AVAILABLE",
                current_process_id=None,
                quantity=0,
            )
            db.add(pallet)
            pallet_count += 1
    
    db.commit()
    print(f"  + {pallet_count} Pallets created")


def print_summary(db: Session):
    """데이터 요약 출력"""
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
