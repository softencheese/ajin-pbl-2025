
import asyncio
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User

async def verify_auth_bypass():
    print(f"Current AUTH_ENABLED setting: {settings.AUTH_ENABLED}")
    
    # 1. Test Bypass Mode
    if not settings.AUTH_ENABLED:
        print("Checking Bypass Mode...")
        user = await get_current_user(token=None, db=None)
        print(f"Result User: {user.username}, Role: {user.role}, Name: {user.full_name}")
        assert user.username == "admin_bypass"
        assert user.role == "ADMIN"
        print("✅ Bypass Mode Verified!")
    else:
        print("AUTH_ENABLED is True. Skipping Bypass Test.")

if __name__ == "__main__":
    asyncio.run(verify_auth_bypass())
