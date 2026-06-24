"""Add missing columns that exist in SQLAlchemy models but not in Database_Schema.sql."""
import asyncio
import asyncpg

DB_URL = "postgresql://postgres:123456@localhost:9999/sms_dbn"

PATCHES = [
    # users table - missing first_name, last_name
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(100)",
    # school_profile - might be missing some columns
    "ALTER TABLE school_profile ADD COLUMN IF NOT EXISTS school_name_regional TEXT",
]

async def main():
    conn = await asyncpg.connect(DB_URL)
    for sql in PATCHES:
        try:
            await conn.execute(sql)
            print(f"✓ {sql[:80]}")
        except Exception as e:
            print(f"✗ {sql[:80]}: {e}")
    await conn.close()
    print("Done")

asyncio.run(main())
