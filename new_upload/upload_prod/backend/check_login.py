import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv()

async def main():
    url = os.getenv('DATABASE_URL','').replace('postgresql+asyncpg','postgresql')
    conn = await asyncpg.connect(url)
    rows = await conn.fetch("SELECT email, is_active FROM users LIMIT 10")
    for r in rows:
        print(dict(r))
    await conn.close()

asyncio.run(main())
