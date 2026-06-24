"""
Seed script — Vendor Inventory permissions and vendor role.
Run once after migration: python seed_vendor_inventory.py
"""
import asyncio
import sys
import uuid
from sqlalchemy import text

# ── permission definitions ────────────────────────────────────────────
VENDOR_PERMISSIONS = [
    ("vendor_inventory", "view",   "View vendor inventory data"),
    ("vendor_inventory", "manage", "Manage vendor inventory (CRUD)"),
]

# Roles that get each permission
# Format: {permission_key: [role_names]}
ROLE_PERMISSION_MAP = {
    ("vendor_inventory", "view"):   ["Super Admin", "School Admin", "Principal", "Accountant", "vendor"],
    ("vendor_inventory", "manage"): ["Super Admin", "School Admin", "Principal", "Accountant"],
}

VENDOR_ROLE = {
    "name": "vendor",
    "description": "Third-party vendor — can view their own inventory and sales data",
}


async def seed():
    from app.db.session import async_session_factory
    async with async_session_factory() as db:
        # 1. Ensure permissions exist
        for module, action, description in VENDOR_PERMISSIONS:
            existing = await db.execute(
                text("SELECT id FROM permissions WHERE module = :m AND action = :a"),
                {"m": module, "a": action},
            )
            row = existing.fetchone()
            if not row:
                perm_id = str(uuid.uuid4())
                await db.execute(
                    text("INSERT INTO permissions (id, module, action, description) VALUES (:id, :m, :a, :d)"),
                    {"id": perm_id, "m": module, "a": action, "d": description},
                )
                print(f"  Created permission: {module}:{action}")
            else:
                perm_id = str(row[0])
                print(f"  Permission already exists: {module}:{action}")

        # 2. Ensure vendor role exists
        existing_role = await db.execute(
            text("SELECT id FROM roles WHERE name = :n"),
            {"n": VENDOR_ROLE["name"]},
        )
        role_row = existing_role.fetchone()
        if not role_row:
            vendor_role_id = str(uuid.uuid4())
            await db.execute(
                text("INSERT INTO roles (id, name, slug, description, is_system, is_active, created_at, updated_at) "
                     "VALUES (:id, :n, :s, :d, 0, 1, GETDATE(), GETDATE())"),
                {"id": vendor_role_id, "n": VENDOR_ROLE["name"], "s": VENDOR_ROLE["name"].lower(), "d": VENDOR_ROLE["description"]},
            )
            print(f"  Created role: {VENDOR_ROLE['name']}")
        else:
            vendor_role_id = str(role_row[0])
            print(f"  Role already exists: {VENDOR_ROLE['name']}")

        # 3. Assign permissions to roles
        for (module, action), role_names in ROLE_PERMISSION_MAP.items():
            # Get permission id
            perm_row = await db.execute(
                text("SELECT id FROM permissions WHERE module = :m AND action = :a"),
                {"m": module, "a": action},
            )
            perm_id = str(perm_row.fetchone()[0])

            for role_name in role_names:
                role_row = await db.execute(
                    text("SELECT id FROM roles WHERE name = :n"),
                    {"n": role_name},
                )
                r = role_row.fetchone()
                if not r:
                    print(f"  WARNING: role '{role_name}' not found, skipping")
                    continue
                role_id = str(r[0])

                # Check if link exists
                link = await db.execute(
                    text("SELECT 1 FROM role_permissions WHERE role_id = :r AND permission_id = :p"),
                    {"r": role_id, "p": perm_id},
                )
                if not link.fetchone():
                    await db.execute(
                        text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:r, :p)"),
                        {"r": role_id, "p": perm_id},
                    )
                    print(f"    Linked {role_name} → {module}:{action}")
                else:
                    print(f"    Already linked: {role_name} → {module}:{action}")

        await db.commit()
        print("\nDone — vendor inventory permissions seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
