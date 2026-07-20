import asyncio, asyncpg

DB_URL = "postgresql://sms_db_lkbf_user:NIORFqrNXuQOn5ELyvq2115XFJ1i0Qot@dpg-d7lileegvqtc73f52v6g-a.oregon-postgres.render.com/sms_db_lkbf"
    tables = ['students','student_enrollments','fee_invoices','fee_payments',
              'student_attendance','staff','staff_attendance','income_records',
              'expense_records','income_categories','expense_categories','departments','designations']
    for t in tables:
        sql = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{t}' ORDER BY ordinal_position"
        try:
            cols = await conn.fetch(sql)
            print(f"{t}: {[r['column_name'] for r in cols]}")
        except Exception as e:
            print(f"{t}: ERROR {e}")
    await conn.close()

asyncio.run(main())
