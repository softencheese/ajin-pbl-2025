import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def recreate_admin():
    db = SessionLocal()
    try:
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="Administrator",
            role="ADMIN",
            is_active=True,
            permissions={}
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user recreated!")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    recreate_admin()
