import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://postgres:123456@localhost:9999/sms_dbn')
    tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    print('Tables:', [r['tablename'] for r in tables])
    try:
        users = await conn.fetch('SELECT username, is_active FROM users LIMIT 5')
        print('Users:', [(r['username'], r['is_active']) for r in users])
    except Exception as e:
        print('No users table:', e)
    await conn.close()

asyncio.run(check())
