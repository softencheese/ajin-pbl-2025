from app.core.database import SessionLocal
from app.models.pallet import Pallet

db = SessionLocal()
pallets = db.query(Pallet).filter(Pallet.current_process_id == 3).all()
for p in pallets:
    print(f"ID: {p.id}, No: {p.pallet_no}, Status: {p.status}, Proc: {p.current_process_id}")
db.close()
