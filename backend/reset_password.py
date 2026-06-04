"""Reset admin password to a known value for testing."""
import asyncio
import asyncpg
import os
import bcrypt
from dotenv import load_dotenv

load_dotenv()

async def main():
    url = os.getenv('DATABASE_URL', '').replace('postgresql+asyncpg', 'postgresql')
    conn = await asyncpg.connect(url)

    # Check users with school_id (non-superadmin)
    rows = await conn.fetch("SELECT id, email, username, school_id FROM users WHERE is_active = true AND school_id IS NOT NULL LIMIT 5")
    print("School users:")
    for r in rows:
        print(dict(r))

    # Reset password for ravi.kumar@stonevalley.edu
    new_hash = bcrypt.hashpw(b"Admin@123", bcrypt.gensalt()).decode()
    updated = await conn.execute(
        "UPDATE users SET password_hash = $1 WHERE email = $2",
        new_hash, "ravi.kumar@stonevalley.edu"
    )
    print(f"\nReset password for ravi.kumar@stonevalley.edu: {updated}")

    # Also reset principal
    updated2 = await conn.execute(
        "UPDATE users SET password_hash = $1 WHERE email = $2",
        new_hash, "principal@stonevalley.edu"
    )
    print(f"Reset password for principal@stonevalley.edu: {updated2}")

    await conn.close()
    print("\nDone. Login with Admin@123")

asyncio.run(main())
