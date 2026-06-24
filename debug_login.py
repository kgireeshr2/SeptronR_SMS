import asyncio
import asyncpg
import bcrypt

DB_URL = "postgresql://sms_db_lkbf_user:NIORFqrNXuQOn5ELyvq2115XFJ1i0Qot@dpg-d7lileegvqtc73f52v6g-a.oregon-postgres.render.com/sms_db_lkbf"

async def main():
    conn = await asyncpg.connect(DB_URL)
    
    # Check purushotham
    row = await conn.fetchrow("SELECT username, password_hash, is_active, school_id FROM users WHERE username='purushotham'")
    if row:
        print(f"Found user: {row['username']}, active={row['is_active']}, school_id={row['school_id']}")
        pw_hash = row['password_hash']
        print(f"Hash: {pw_hash[:30]}...")
        result = bcrypt.checkpw('123456'.encode('utf-8'), pw_hash.encode('utf-8'))
        print(f"bcrypt.checkpw('123456', hash): {result}")
    else:
        print("User 'purushotham' NOT FOUND in DB")
    
    print()
    
    # Check superadmin
    row2 = await conn.fetchrow("SELECT username, password_hash, is_active, is_super_admin, school_id FROM users WHERE username='superadmin'")
    if row2:
        print(f"Found superadmin: {row2['username']}, active={row2['is_active']}, is_super_admin={row2['is_super_admin']}, school_id={row2['school_id']}")
        result2 = bcrypt.checkpw('12345678'.encode('utf-8'), row2['password_hash'].encode('utf-8'))
        print(f"bcrypt.checkpw('12345678', hash): {result2}")
    else:
        print("User 'superadmin' NOT FOUND")
    
    await conn.close()

asyncio.run(main())
