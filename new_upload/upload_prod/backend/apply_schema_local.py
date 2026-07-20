"""
Apply Database_Schema.sql to local DB, stamp alembic to current heads,
then seed the superadmin user.
"""
import asyncio
import os
import sys
import asyncpg

DB_URL = "postgresql://postgres:123456@localhost:9999/sms_dbn"
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), '..', 'Database_Schema.sql')

async def apply_schema():
    conn = await asyncpg.connect(DB_URL)
    try:
        sql = open(SCHEMA_FILE, encoding='utf-8').read()
        print("Applying schema SQL...")
        await conn.execute(sql)
        print("✓ Schema applied successfully")
    except Exception as e:
        print(f"✗ Schema error: {e}")
        raise
    finally:
        await conn.close()

asyncio.run(apply_schema())
