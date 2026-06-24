"""
Seed initial data:
- Platform permissions
- System roles (with permissions)
- Super admin user
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import async_session_factory
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.auth import User
from app.models.rbac import Role, Permission, RolePermission, UserRole
import uuid


# ─────────────────────────────────────────────────────────────────────────────
# PLATFORM PERMISSIONS (105 permissions across all modules)
# Format: (module, action, description)
# ─────────────────────────────────────────────────────────────────────────────
ALL_PERMISSIONS = [
    # Users
    ("users", "view", "View users"),
    ("users", "create", "Create users"),
    ("users", "edit", "Edit users"),
    ("users", "delete", "Delete users"),
    
    # Roles
    ("roles", "view", "View roles"),
    ("roles", "create", "Create roles"),
    ("roles", "edit", "Edit roles"),
    ("roles", "delete", "Delete roles"),
    ("roles", "manage", "Manage role permissions"),
    
    # Academic Years
    ("academic_years", "view", "View academic years"),
    ("academic_years", "create", "Create academic years"),
    ("academic_years", "edit", "Edit academic years"),
    ("academic_years", "delete", "Delete academic years"),
    
    # Admissions
    ("admissions", "view", "View admission applications"),
    ("admissions", "create", "Create admission forms"),
    ("admissions", "edit", "Edit admission forms"),
    ("admissions", "delete", "Delete admission forms"),
    ("admissions", "approve", "Approve/Reject applications"),
    
    # Classes
    ("classes", "view", "View classes"),
    ("classes", "create", "Create classes"),
    ("classes", "edit", "Edit classes"),
    ("classes", "delete", "Delete classes"),
    
    # Sections
    ("sections", "view", "View sections"),
    ("sections", "create", "Create sections"),
    ("sections", "edit", "Edit sections"),
    ("sections", "delete", "Delete sections"),
    
    # Subjects
    ("subjects", "view", "View subjects"),
    ("subjects", "create", "Create subjects"),
    ("subjects", "edit", "Edit subjects"),
    ("subjects", "delete", "Delete subjects"),
    
    # Timetable
    ("timetable", "view", "View timetable"),
    ("timetable", "create", "Create timetable"),
    ("timetable", "edit", "Edit timetable"),
    
    # Students
    ("students", "view", "View students"),
    ("students", "create", "Admit students"),
    ("students", "edit", "Edit student records"),
    ("students", "delete", "Delete students"),
    ("students", "export", "Export student data"),
    
    # Staff
    ("staff", "view", "View staff"),
    ("staff", "create", "Create staff"),
    ("staff", "edit", "Edit staff"),
    ("staff", "delete", "Delete staff"),
    ("staff", "export", "Export staff data"),
    
    # Attendance
    ("attendance", "view", "View attendance"),
    ("attendance", "create", "Mark attendance"),
    ("attendance", "edit", "Edit attendance"),
    ("attendance", "export", "Export attendance reports"),
    
    # Fees
    ("fees", "view", "View fee records"),
    ("fees", "create", "Create fee structures"),
    ("fees", "edit", "Edit fees"),
    ("fees", "delete", "Delete fees"),
    ("fees", "collect", "Collect fee payments"),
    ("fees", "export", "Export fee reports"),
    
    # Exams
    ("exams", "view", "View exams"),
    ("exams", "create", "Create exams"),
    ("exams", "edit", "Edit exams and marks"),
    ("exams", "delete", "Delete exams"),
    ("exams", "publish", "Publish exam results"),
    
    # Library
    ("library", "view", "View library"),
    ("library", "create", "Add books"),
    ("library", "edit", "Edit library records"),
    ("library", "delete", "Delete books"),
    
    # Transport
    ("transport", "view", "View transport"),
    ("transport", "create", "Add transport"),
    ("transport", "edit", "Edit transport"),
    ("transport", "delete", "Delete transport"),
    
    # Inventory
    ("inventory", "view", "View inventory"),
    ("inventory", "create", "Add inventory items"),
    ("inventory", "edit", "Edit inventory"),
    ("inventory", "delete", "Delete inventory items"),
    
    # Vendor Inventory
    ("vendor_inventory", "view", "View vendor inventory"),
    ("vendor_inventory", "manage", "Manage vendor inventory"),
    
    # Accounting
    ("accounting", "view", "View accounting records"),
    ("accounting", "create", "Create transactions"),
    ("accounting", "edit", "Edit transactions"),
    ("accounting", "export", "Export accounting reports"),
    
    # Communication
    ("communication", "view", "View messages"),
    ("communication", "create", "Send messages"),
    
    # Homework
    ("homework", "view", "View homework"),
    ("homework", "create", "Assign homework"),
    ("homework", "edit", "Edit homework"),
    ("homework", "delete", "Delete homework"),
    
    # PTM
    ("ptm", "view", "View PTM events"),
    ("ptm", "create", "Create PTM events"),
    ("ptm", "manage", "Manage PTM bookings"),
    
    # Calendar
    ("calendar", "view", "View calendar"),
    ("calendar", "create", "Create events"),
    ("calendar", "edit", "Edit events"),
    
    # Reports
    ("reports", "view", "View reports"),
    ("reports", "export", "Export reports"),
    
    # Settings
    ("settings", "view", "View settings"),
    ("settings", "edit", "Edit settings"),
    
    # Audit Logs
    ("audit", "view", "View audit logs"),

    # Public Website
    ("website", "view", "View website settings"),
    ("website", "create", "Create website content"),
    ("website", "update", "Update website content"),
    ("website", "delete", "Delete website content"),
    ("website", "publish", "Publish/unpublish website"),
    ("enquiries", "view", "View enquiries"),
    ("enquiries", "update", "Update enquiry status"),
    ("domains", "view", "View custom domains"),
    ("domains", "manage", "Manage custom domains"),

    # Dashboard
    ("dashboard", "view", "View dashboard"),
]


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM ROLES & THEIR PERMISSIONS
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_ROLES = {
    "super_admin": {
        "name": "Super Admin",
        "description": "Full system access across all schools",
        "permissions": "__all__",  # Special marker for all permissions
    },
    "school_admin": {
        "name": "School Admin",
        "description": "Full access within their school",
        "permissions": "__all__",
    },
    "principal": {
        "name": "Principal",
        "description": "Academic oversight, staff management, reports",
        "permissions": [
            "users:view", "users:create", "users:edit",
            "roles:view",
            "academic_years:view", "academic_years:create", "academic_years:edit",
            "admissions:view", "admissions:approve",
            "classes:view", "classes:create", "classes:edit",
            "sections:view", "sections:create", "sections:edit",
            "subjects:view", "subjects:create", "subjects:edit",
            "timetable:view", "timetable:edit",
            "students:view", "students:edit", "students:export",
            "staff:view", "staff:create", "staff:edit", "staff:export",
            "attendance:view", "attendance:export",
            "fees:view", "fees:export",
            "exams:view", "exams:publish",
            "library:view",
            "transport:view",
            "inventory:view",
            "vendor_inventory:view", "vendor_inventory:manage",
            "accounting:view",
            "communication:view", "communication:create",
            "homework:view",
            "ptm:view", "ptm:create", "ptm:manage",
            "calendar:view", "calendar:create", "calendar:edit",
            "reports:view", "reports:export",
            "settings:view",
            "audit:view",
            "website:view", "website:create", "website:update", "website:delete", "website:publish",
            "enquiries:view", "enquiries:update",
            "domains:view", "domains:manage",
            "dashboard:view",
        ],
    },
    "vice_principal": {
        "name": "Vice Principal",
        "description": "Support principal with academic operations",
        "permissions": [
            "academic_years:view",
            "admissions:view",
            "classes:view",
            "sections:view",
            "subjects:view",
            "timetable:view", "timetable:edit",
            "students:view", "students:edit",
            "staff:view",
            "attendance:view", "attendance:export",
            "fees:view",
            "exams:view",
            "communication:view", "communication:create",
            "homework:view",
            "ptm:view",
            "calendar:view",
            "reports:view", "reports:export",
            "dashboard:view",
        ],
    },
    "teacher": {
        "name": "Teacher",
        "description": "Mark attendance, enter marks, assign homework",
        "permissions": [
            "timetable:view",
            "students:view",
            "attendance:view", "attendance:create", "attendance:edit",
            "exams:view", "exams:edit",
            "homework:view", "homework:create", "homework:edit",
            "communication:view",
            "calendar:view",
            "dashboard:view",
        ],
    },
    "class_teacher": {
        "name": "Class Teacher",
        "description": "Teacher with additional class management",
        "permissions": [
            "timetable:view",
            "students:view", "students:edit",
            "attendance:view", "attendance:create", "attendance:edit", "attendance:export",
            "exams:view", "exams:edit",
            "homework:view", "homework:create", "homework:edit", "homework:delete",
            "communication:view", "communication:create",
            "ptm:view", "ptm:create", "ptm:manage",
            "calendar:view",
            "reports:view",
            "dashboard:view",
        ],
    },
    "accountant": {
        "name": "Accountant",
        "description": "Manage fees, payments, accounting",
        "permissions": [
            "students:view",
            "staff:view",
            "fees:view", "fees:create", "fees:edit", "fees:collect", "fees:export",
            "accounting:view", "accounting:create", "accounting:edit", "accounting:export",
            "reports:view", "reports:export",
            "dashboard:view",
        ],
    },
    "librarian": {
        "name": "Librarian",
        "description": "Manage library books and issues",
        "permissions": [
            "students:view",
            "staff:view",
            "library:view", "library:create", "library:edit", "library:delete",
            "dashboard:view",
        ],
    },
    "transport_manager": {
        "name": "Transport Manager",
        "description": "Manage vehicles, routes, student transport",
        "permissions": [
            "students:view",
            "transport:view", "transport:create", "transport:edit", "transport:delete",
            "dashboard:view",
        ],
    },
    "inventory_manager": {
        "name": "Inventory Manager",
        "description": "Manage school inventory and supplies",
        "permissions": [
            "inventory:view", "inventory:create", "inventory:edit", "inventory:delete",
            "vendor_inventory:view", "vendor_inventory:manage",
            "dashboard:view",
        ],
    },
    "receptionist": {
        "name": "Receptionist",
        "description": "Front desk operations, visitor management",
        "permissions": [
            "admissions:view",
            "students:view",
            "staff:view",
            "communication:view",
            "calendar:view",
            "enquiries:view", "enquiries:update",
            "dashboard:view",
        ],
    },
    "parent": {
        "name": "Parent",
        "description": "View child's records via parent portal",
        "permissions": [
            "students:view",
            "attendance:view",
            "fees:view",
            "exams:view",
            "timetable:view",
            "homework:view",
            "communication:view",
            "calendar:view",
            "dashboard:view",
        ],
    },
    "student": {
        "name": "Student",
        "description": "View own academic records",
        "permissions": [
            "attendance:view",
            "fees:view",
            "exams:view",
            "timetable:view",
            "homework:view",
            "communication:view",
            "calendar:view",
            "dashboard:view",
        ],
    },
}


async def seed_permissions(db: AsyncSession) -> dict[str, uuid.UUID]:
    """Seed all platform permissions and return module:action -> id mapping"""
    print("  → Seeding permissions...")
    perm_map: dict[str, uuid.UUID] = {}

    for module, action, description in ALL_PERMISSIONS:
        result = await db.execute(
            select(Permission).where(
                Permission.module == module,
                Permission.action == action
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            perm = Permission(
                id=uuid.uuid4(),
                module=module,
                action=action,
                description=description,
            )
            db.add(perm)
            await db.flush()
            perm_map[f"{module}:{action}"] = perm.id
        else:
            perm_map[f"{module}:{action}"] = existing.id

    await db.commit()
    print(f"     ✓ {len(perm_map)} permissions ready")
    return perm_map


async def seed_roles(db: AsyncSession, perm_map: dict[str, uuid.UUID]) -> dict[str, uuid.UUID]:
    """Seed system roles with their permissions and return slug -> id mapping"""
    print("  → Seeding system roles...")
    role_map: dict[str, uuid.UUID] = {}
    all_perm_slugs = list(perm_map.keys())

    for role_slug, data in SYSTEM_ROLES.items():
        # Create or get role
        result = await db.execute(select(Role).where(Role.slug == role_slug))
        existing = result.scalar_one_or_none()
        
        if not existing:
            role = Role(
                id=uuid.uuid4(),
                school_id=None,  # Platform-level roles
                name=data["name"],
                slug=role_slug,
                description=data["description"],
                is_system=True,
                is_active=True,
            )
            db.add(role)
            await db.flush()
            role_map[role_slug] = role.id
        else:
            role_map[role_slug] = existing.id

        # Assign permissions
        role_id = role_map[role_slug]
        perm_slugs = all_perm_slugs if data["permissions"] == "__all__" else data["permissions"]
        
        for perm_slug in perm_slugs:
            if perm_slug not in perm_map:
                continue
            
            perm_id = perm_map[perm_slug]
            
            # Check if already assigned
            result = await db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == perm_id,
                )
            )
            if not result.scalar_one_or_none():
                db.add(RolePermission(role_id=role_id, permission_id=perm_id))

    await db.commit()
    print(f"     ✓ {len(role_map)} roles ready with permissions")
    return role_map


async def seed_super_admin(db: AsyncSession, role_map: dict[str, uuid.UUID]):
    """Create super admin user"""
    print("  → Seeding super admin user...")

    sa_email = getattr(settings, "SUPER_ADMIN_EMAIL", "superadmin@sms.com")
    sa_username = getattr(settings, "SUPER_ADMIN_USERNAME", "superadmin")
    sa_password = getattr(settings, "SUPER_ADMIN_PASSWORD", "SuperAdmin@123")

    # Check if exists
    result = await db.execute(select(User).where(User.email == sa_email))
    existing = result.scalar_one_or_none()

    if existing:
        print(f"     ✓ Super admin already exists: {sa_email}")
        return

    # Create super admin
    sa_user = User(
        id=uuid.uuid4(),
        school_id=None,  # Super admin not tied to any school
        username=sa_username,
        email=sa_email,
        phone=None,
        password_hash=get_password_hash(sa_password),
        first_name="Super",
        last_name="Admin",
        is_active=True,
        is_verified=True,
        is_super_admin=True,
    )
    db.add(sa_user)
    await db.flush()

    # Assign super_admin role
    super_admin_role_id = role_map.get("super_admin")
    if super_admin_role_id:
        db.add(UserRole(
            user_id=sa_user.id,
            role_id=super_admin_role_id,
        ))

    await db.commit()
    print(f"     ✓ Super admin created: {sa_email} / {sa_password}")


async def main():
    print("\n🌱 Starting seed process...\n")
    
    async with async_session_factory() as db:
        try:
            # 1. Seed permissions
            perm_map = await seed_permissions(db)
            
            # 2. Seed roles with permissions
            role_map = await seed_roles(db, perm_map)
            
            # 3. Seed super admin
            await seed_super_admin(db, role_map)
            
            print("\n✅ Seed completed successfully!\n")
            print("=" * 60)
            print("  Super Admin Credentials:")
            print(f"  Email:    {getattr(settings, 'SUPER_ADMIN_EMAIL', 'superadmin@sms.com')}")
            print(f"  Username: {getattr(settings, 'SUPER_ADMIN_USERNAME', 'superadmin')}")
            print(f"  Password: {getattr(settings, 'SUPER_ADMIN_PASSWORD', 'SuperAdmin@123')}")
            print(f"\n  API Docs: http://localhost:8000/docs")
            print("=" * 60 + "\n")
            
        except Exception as e:
            print(f"\n❌ Seed failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
