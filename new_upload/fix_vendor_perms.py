import psycopg2
from itertools import groupby

conn = psycopg2.connect('postgresql://sms_db_lkbf_user:NIORFqrNXuQOn5ELyvq2115XFJ1i0Qot@dpg-d7lileegvqtc73f52v6g-a.oregon-postgres.render.com/sms_db_lkbf')
cur = conn.cursor()

# Find all vendor_inventory permissions
cur.execute("SELECT id, module, action FROM permissions WHERE module = 'vendor_inventory' ORDER BY action, id")
perms = cur.fetchall()
print('All vendor_inventory permissions:')
for p in perms:
    print(p)

# Keep the first of each action, delete the rest
to_delete = []
to_keep = []
for action, group in groupby(perms, key=lambda x: x[2]):
    items = list(group)
    to_keep.append(items[0][0])
    for item in items[1:]:
        to_delete.append(item[0])

print(f'\nKeeping: {to_keep}')
print(f'Deleting duplicates: {to_delete}')

if to_delete:
    cur.execute('DELETE FROM role_permissions WHERE permission_id = ANY(%s)', (to_delete,))
    print(f'role_permissions rows removed: {cur.rowcount}')
    cur.execute('DELETE FROM permissions WHERE id = ANY(%s)', (to_delete,))
    print(f'permissions rows removed: {cur.rowcount}')

conn.commit()

# Verify final state
cur.execute("""
    SELECT r.slug, p.module, p.action
    FROM role_permissions rp
    JOIN roles r ON r.id = rp.role_id
    JOIN permissions p ON p.id = rp.permission_id
    WHERE p.module = 'vendor_inventory'
    ORDER BY r.slug, p.action
""")
print('\nFinal state:')
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()
print('\nDone.')
