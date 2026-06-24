"""Debug login by calling auth logic directly and capturing any exception."""
import asyncio
import traceback
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:123456@localhost:9999/sms_dbn")
os.environ.setdefault("SECRET_KEY", "dev-secret-key-local")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("REDIS_ENABLED", "false")

async def main():
    try:
        from app.db.session import async_session_factory
        from app.services.auth_service import AuthService

        async with async_session_factory() as db:
            service = AuthService(db, None)  # no redis
            result, refresh_token, jti = await service.login("superadmin", "12345678", None)
            print("Login OK:", result.user.username, "is_super_admin:", result.user.is_super_admin)
    except Exception as e:
        print("ERROR:", type(e).__name__, str(e))
        traceback.print_exc()

asyncio.run(main())
