from app.core.database import SessionLocal
from app.models.pallet import Pallet
from app.models.physical_pallet import PhysicalPallet

db = SessionLocal()
p = db.query(Pallet).filter(Pallet.pallet_no == "PLT-260221-0003").first()
if p:
    print(f"Pallet No: {p.pallet_no}")
    print(f"Status: {p.status}")
    print(f"Quantity: {p.quantity}")
    print(f"LOT ID: {p.lot_id}")
    
    pp = db.query(PhysicalPallet).filter(PhysicalPallet.id == p.physical_pallet_id).first()
    if pp:
        print(f"EPC: {pp.epc}")

db.close()
