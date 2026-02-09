import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import engine, Base
from app.models.process import Process
from app.models.item import Item
from app.models.rfid import RFIDReaderLocation
from app.models.lot import Lot
from app.models.pallet import Pallet
from app.models.user import User

def drop_all():
    print("🔥 Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped!")

if __name__ == "__main__":
    drop_all()
