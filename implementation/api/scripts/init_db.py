import sys
import os

# Add the parent directory to sys.path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.process import Process
from app.models.item import Item
from app.models.rfid import RFIDReaderLocation
from app.models.lot import Lot
from datetime import date, datetime

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        create_processes(db)
        create_items(db)
        create_reader_locations(db)
        # create_sample_lots(db) # Optional: Uncomment to create sample lots
        print("Initial data seeding completed successfully.")
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

def create_processes(db: Session):
    print("Creating processes...")
    processes = [
        {
            "process_code": "SHEARING_400T",
            "process_name": "샤링",
            "process_order": 1,
            "production_line": "400T"
        },
        {
            "process_code": "PRESS_1500T",
            "process_name": "프레스",
            "process_order": 2,
            "production_line": "본사 1500T"
        },
        {
            "process_code": "ASSEMBLY_A",
            "process_name": "조립",
            "process_order": 3,
            "production_line": "Line-A"
        },
        {
            "process_code": "SHIPPING",
            "process_name": "출하",
            "process_order": 4,
            "production_line": "Shipping Dock"
        }
    ]

    for p_data in processes:
        existing = db.query(Process).filter(Process.process_code == p_data["process_code"]).first()
        if not existing:
            process = Process(**p_data)
            db.add(process)
            print(f"Added process: {p_data['process_name']} ({p_data['production_line']})")
    db.commit()

def create_items(db: Session):
    print("Creating items...")
    items = [
        # Image 1 Data
        {
            "item_code": "C059461B",
            "item_name": "Shell Coil C059461B",
            "item_type": "RAW",
            "unit": "KG",
            "vehicle_model": "JX1",
            "spec": "Initial Coil"
        },
        {
            "item_code": "71412-T6000S",
            "item_name": "PNL-OTR, RH", # Guessing name based on code pattern or generic
            "item_type": "WIP",
            "unit": "EA",
            "vehicle_model": "JX1",
            "spec": "Sheared Panel"
        },
        # Image 2 Data
        {
            "item_code": "AS89464A",
            "item_name": "Shell Coil AS89464A",
            "item_type": "RAW",
            "unit": "KG",
            "vehicle_model": "NE",
            "spec": "Input Sheet Coil"
        },
        {
            "item_code": "76211-GI000",
            "item_name": "PNL-FR DR INR, LH",
            "item_type": "WIP", # or PRODUCT depending on point of view, usually press part is WIP
            "unit": "EA",
            "vehicle_model": "NE",
            "spec": "Press Part"
        }
    ]

    for i_data in items:
        existing = db.query(Item).filter(Item.item_code == i_data["item_code"]).first()
        if not existing:
            item = Item(**i_data)
            db.add(item)
            print(f"Added item: {i_data['item_code']} ({i_data['item_name']})")
    db.commit()

def create_reader_locations(db: Session):
    print("Creating reader locations...")
    # Map readers to processes
    # We need to fetch process IDs first
    shearing = db.query(Process).filter(Process.process_code == "SHEARING_400T").first()
    press = db.query(Process).filter(Process.process_code == "PRESS_1500T").first()
    assembly = db.query(Process).filter(Process.process_code == "ASSEMBLY_A").first()
    
    locations = [
        {
            "port_name": "COM1",
            "process_id": shearing.id if shearing else None,
            "location_type": "IN",
            "description": "샤링 400T 투입 (가상)"
        },
        {
            "port_name": "COM2",
            "process_id": shearing.id if shearing else None,
            "location_type": "OUT",
            "description": "샤링 400T 배출 (가상)"
        },
        {
            "port_name": "COM3",
            "process_id": press.id if press else None,
            "location_type": "IN",
            "description": "프레스 1500T 투입 (가상)"
        },
        {
            "port_name": "COM4",
            "process_id": press.id if press else None,
            "location_type": "OUT",
            "description": "프레스 1500T 배출 (가상)"
        },
        {
            "port_name": "COM5",
            "process_id": assembly.id if assembly else None,
            "location_type": "IN",
            "description": "조립 Line-A 투입 (가상)"
        },
        {
            "port_name": "COM6",
            "process_id": assembly.id if assembly else None,
            "location_type": "OUT",
            "description": "조립 Line-A 배출 (완제품) (가상)"
        }
    ]

    for l_data in locations:
        if not l_data["process_id"]:
            continue
            
        existing = db.query(RFIDReaderLocation).filter(RFIDReaderLocation.port_name == l_data["port_name"]).first()
        if not existing:
            location = RFIDReaderLocation(**l_data)
            db.add(location)
            print(f"Added reader location: {l_data['port_name']} -> {l_data['description']}")
    db.commit()

if __name__ == "__main__":
    init_db()
