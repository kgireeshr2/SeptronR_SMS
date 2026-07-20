import asyncio, os, sys
sys.path.insert(0, r'c:\Users\2098069\Downloads\Personal\Repo\SMS\backend')
from dotenv import load_dotenv
load_dotenv(r'c:\Users\2098069\Downloads\Personal\Repo\SMS\backend\.env')
import asyncpg

async def main():
    url = os.getenv('DATABASE_URL', '').replace('postgresql+asyncpg://', '')
    conn = await asyncpg.connect('postgresql://' + url)

    exists = await conn.fetchval(
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='personal_expenses' AND column_name='paid_amount'"
    )
    print('paid_amount column exists:', bool(exists))

    if not exists:
        await conn.execute("ALTER TABLE personal_expenses ADD COLUMN paid_amount NUMERIC(12,2) NOT NULL DEFAULT 0")
        await conn.execute("UPDATE personal_expenses SET paid_amount = amount WHERE status = 'paid'")
        print('Column added and backfilled.')
    
    has_partial = await conn.fetchval(
        "SELECT COUNT(*) FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'personal_expense_status' AND e.enumlabel = 'partial'"
    )
    print('partial enum value exists:', bool(has_partial))
    if not has_partial:
        await conn.execute("ALTER TYPE personal_expense_status ADD VALUE IF NOT EXISTS 'partial' BEFORE 'paid'")
        print('partial enum value added.')

    await conn.close()
    print('All done.')

asyncio.run(main())
