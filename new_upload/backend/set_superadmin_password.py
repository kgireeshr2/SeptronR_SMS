"""Reset superadmin password to 12345678 for local testing."""
import asyncio
import asyncpg
import bcrypt

DB_URL = "postgresql://postgres:123456@localhost:9999/sms_dbn"

async def main():
    conn = await asyncpg.connect(DB_URL)
    new_hash = bcrypt.hashpw(b"12345678", bcrypt.gensalt()).decode()
    result = await conn.execute(
        "UPDATE users SET password_hash = $1 WHERE username = 'superadmin'",
        new_hash
    )
    print(f"Updated: {result}")
    row = await conn.fetchrow("SELECT username, is_active, is_super_admin FROM users WHERE username = 'superadmin'")
    print(f"Superadmin: {dict(row)}")
    await conn.close()
    print("Done. Login: superadmin / 12345678")

asyncio.run(main())
