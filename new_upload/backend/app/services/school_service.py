"""School service: handles school creation and default seeding."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.rbac import Role, Permission, RolePermission
from app.repositories.role_repository import RoleRepository
from app.data.default_templates import DEFAULT_DOCUMENT_TEMPLATES, DEFAULT_NOTIFICATION_TEMPLATES


# All permissions in the system: (module, action)
ALL_PERMISSIONS: list[tuple[str, str]] = [
    # Auth / Users
    ("users", "view"), ("users", "create"), ("users", "update"), ("users", "delete"), ("users", "manage"),
    # Roles
    ("roles", "view"), ("roles", "create"), ("roles", "update"), ("roles", "delete"), ("roles", "manage"),
    # Academic Year
    ("academic_years", "view"), ("academic_years", "create"), ("academic_years", "update"), ("academic_years", "delete"),
    # Admissions
    ("admissions", "view"), ("admissions", "create"), ("admissions", "update"), ("admissions", "delete"), ("admissions", "approve"),
    # Classes / Sections
    ("classes", "view"), ("classes", "create"), ("classes", "update"), ("classes", "delete"),
    ("sections", "view"), ("sections", "create"), ("sections", "update"), ("sections", "delete"),
    # Subjects
    ("subjects", "view"), ("subjects", "create"), ("subjects", "update"), ("subjects", "delete"),
    # Timetable
    ("timetable", "view"), ("timetable", "create"), ("timetable", "update"), ("timetable", "delete"),
    # Students
    ("students", "view"), ("students", "create"), ("students", "update"), ("students", "delete"), ("students", "export"),
    # Staff
    ("staff", "view"), ("staff", "create"), ("staff", "update"), ("staff", "delete"), ("staff", "export"),
    # Departments
    ("departments", "view"), ("departments", "create"), ("departments", "edit"), ("departments", "delete"),
    # Designations
    ("designations", "view"), ("designations", "create"), ("designations", "edit"), ("designations", "delete"),
    # Leaves
    ("leaves", "view_types"), ("leaves", "create_types"), ("leaves", "edit_types"), ("leaves", "delete_types"),
    ("leaves", "view"), ("leaves", "review"), ("leaves", "view_balances"), ("leaves", "allocate"), ("leaves", "edit_balances"),
    # Payroll
    ("payroll", "view"), ("payroll", "generate"), ("payroll", "edit"), ("payroll", "delete"), ("payroll", "mark_paid"),
    # Attendance (student)
    ("attendance", "view"), ("attendance", "mark"), ("attendance", "report"), ("attendance", "export"),
    # Attendance (staff)
    ("staff_attendance", "view"), ("staff_attendance", "mark"), ("staff_attendance", "report"),
    # Holidays
    ("holidays", "view"), ("holidays", "manage"),
    # Attendance
    ("attendance", "view"), ("attendance", "create"), ("attendance", "update"), ("attendance", "delete"), ("attendance", "approve"), ("attendance", "export"),
    # Fees
    ("fees", "view"), ("fees", "create"), ("fees", "update"), ("fees", "delete"), ("fees", "approve"), ("fees", "export"), ("fees", "manage"), ("fees", "collect"), ("fees", "report"), ("fees", "pay"),
    # Exams
    ("exams", "view"), ("exams", "create"), ("exams", "update"), ("exams", "delete"), ("exams", "approve"), ("exams", "export"),
    # Library
    ("library", "view"), ("library", "create"), ("library", "update"), ("library", "delete"),
    # Transport
    ("transport", "view"), ("transport", "create"), ("transport", "update"), ("transport", "delete"),
    # Inventory
    ("inventory", "view"), ("inventory", "create"), ("inventory", "update"), ("inventory", "delete"),
    # Accounting
    ("accounting", "view"), ("accounting", "create"), ("accounting", "update"), ("accounting", "delete"), ("accounting", "approve"), ("accounting", "export"),
    # Communication
    ("communication", "view"), ("communication", "create"), ("communication", "update"), ("communication", "delete"),
    # Communications (alias used by notification templates endpoint)
    ("communications", "read"), ("communications", "write"), ("communications", "delete"),
    # Templates (document templates)
    ("templates", "read"), ("templates", "write"), ("templates", "delete"),
    # Calendar
    ("calendar", "view"), ("calendar", "create"), ("calendar", "update"), ("calendar", "delete"),
    # Homework
    ("homework", "view"), ("homework", "create"), ("homework", "update"), ("homework", "delete"),
    # PTM
    ("ptm", "view"), ("ptm", "create"), ("ptm", "update"), ("ptm", "delete"),
    # Reports
    ("reports", "view"), ("reports", "export"),
    # Audit Logs
    ("audit_logs", "view"),
    # Settings
    ("settings", "view"), ("settings", "update"), ("settings", "manage"),
    # Public Website
    ("website", "view"), ("website", "create"), ("website", "update"), ("website", "delete"), ("website", "publish"),
    ("enquiries", "view"), ("enquiries", "update"),
    ("domains", "view"), ("domains", "manage"),
    # Dashboard
    ("dashboard", "view"),
]

# Role → allowed permission slugs
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "school_admin": [f"{m}:{a}" for m, a in ALL_PERMISSIONS],  # all permissions
    "principal": [
        "users:view", "users:create", "users:update",
        "academic_years:view", "admissions:view", "admissions:approve",
        "classes:view", "sections:view", "subjects:view", "timetable:view",
        "students:view", "students:export",
        "staff:view", "staff:export",
        "attendance:view", "attendance:mark", "attendance:report", "attendance:approve", "attendance:export",
        "staff_attendance:view", "staff_attendance:mark", "staff_attendance:report",
        "holidays:view", "holidays:manage",
        "fees:view", "fees:approve", "fees:export", "fees:report",
        "exams:view", "exams:approve", "exams:export",
        "library:view", "transport:view", "inventory:view",
        "accounting:view", "accounting:export",
        "communication:view", "communication:create",
        "communications:read", "communications:write",
        "templates:read", "templates:write", "templates:delete",
        "calendar:view", "calendar:create",
        "homework:view", "ptm:view",
        "reports:view", "reports:export",
        "audit_logs:view", "settings:view",
        "website:view", "website:create", "website:update", "website:delete", "website:publish",
        "enquiries:view", "enquiries:update",
        "domains:view", "domains:manage",
        "dashboard:view",
    ],
    "vice_principal": [
        "users:view", "academic_years:view",
        "classes:view", "sections:view", "subjects:view", "timetable:view",
        "students:view", "students:export",
        "staff:view",
        "attendance:view", "attendance:mark", "attendance:report", "attendance:approve", "attendance:export",
        "staff_attendance:view", "staff_attendance:report",
        "holidays:view",
        "fees:view", "fees:export", "fees:report",
        "exams:view", "exams:approve", "exams:export",
        "communication:view", "communication:create",
        "communications:read", "communications:write",
        "templates:read", "templates:write",
        "calendar:view", "calendar:create",
        "homework:view", "ptm:view",
        "reports:view", "reports:export",
        "dashboard:view",
    ],
    "teacher": [
        "students:view",
        "attendance:view", "attendance:create", "attendance:update", "attendance:mark",
        "holidays:view",
        "exams:view", "exams:create", "exams:update",
        "homework:view", "homework:create", "homework:update",
        "communication:view", "communication:create",
        "calendar:view",
        "timetable:view",
        "subjects:view",
        "ptm:view", "ptm:create",
        "dashboard:view",
    ],
    "class_teacher": [
        "students:view",
        "attendance:view", "attendance:create", "attendance:update", "attendance:mark",
        "holidays:view",
        "exams:view", "exams:create", "exams:update",
        "homework:view", "homework:create", "homework:update",
        "communication:view", "communication:create",
        "calendar:view",
        "timetable:view",
        "subjects:view",
        "fees:view",
        "ptm:view", "ptm:create",
        "dashboard:view",
    ],
    "accountant": [
        "fees:view", "fees:create", "fees:update", "fees:approve", "fees:export", "fees:manage", "fees:collect", "fees:report",
        "accounting:view", "accounting:create", "accounting:update", "accounting:approve", "accounting:export",
        "students:view",
        "reports:view", "reports:export",
        "dashboard:view",
    ],
    "librarian": [
        "library:view", "library:create", "library:update", "library:delete",
        "students:view",
        "dashboard:view",
    ],
    "transport_manager": [
        "transport:view", "transport:create", "transport:update", "transport:delete",
        "students:view",
        "dashboard:view",
    ],
    "inventory_manager": [
        "inventory:view", "inventory:create", "inventory:update", "inventory:delete",
        "dashboard:view",
    ],
    "receptionist": [
        "admissions:view", "admissions:create", "admissions:update",
        "students:view",
        "communication:view", "communication:create",
        "calendar:view",
        "enquiries:view", "enquiries:update",
        "dashboard:view",
    ],
    "parent": [
        "students:view",
        "attendance:view",
        "fees:view", "fees:pay",
        "exams:view",
        "homework:view",
        "communication:view",
        "calendar:view",
        "ptm:view",
        "dashboard:view",
    ],
    "student": [
        "attendance:view",
        "fees:view", "fees:pay",
        "exams:view",
        "homework:view",
        "communication:view",
        "calendar:view",
        "timetable:view",
        "dashboard:view",
    ],
}

SYSTEM_ROLES = [
    {"name": "School Admin", "slug": "school_admin", "description": "Full school access"},
    {"name": "Principal", "slug": "principal", "description": "Principal access"},
    {"name": "Vice Principal", "slug": "vice_principal", "description": "Vice Principal access"},
    {"name": "Teacher", "slug": "teacher", "description": "Teacher access"},
    {"name": "Class Teacher", "slug": "class_teacher", "description": "Class teacher with extended rights"},
    {"name": "Accountant", "slug": "accountant", "description": "Finance and fee management"},
    {"name": "Librarian", "slug": "librarian", "description": "Library management"},
    {"name": "Transport Manager", "slug": "transport_manager", "description": "Transport management"},
    {"name": "Inventory Manager", "slug": "inventory_manager", "description": "Inventory management"},
    {"name": "Receptionist", "slug": "receptionist", "description": "Front desk and admissions"},
    {"name": "Parent", "slug": "parent", "description": "Parent / Guardian portal access"},
    {"name": "Student", "slug": "student", "description": "Student portal access"},
]


async def seed_platform_permissions(db: AsyncSession) -> dict[str, str]:
    """Ensure all platform permissions exist. Returns slug→id mapping."""
    perm_map: dict[str, str] = {}
    for module, action in dict.fromkeys(ALL_PERMISSIONS):
        slug = f"{module}:{action}"
        result = await db.execute(
            select(Permission).where(
                Permission.module == module, Permission.action == action
            )
        )
        existing = result.scalar_one_or_none()
        if not existing:
            perm = Permission(module=module, action=action)
            db.add(perm)
            await db.flush()
            await db.refresh(perm)
            perm_map[slug] = str(perm.id)
        else:
            perm_map[slug] = str(existing.id)
    return perm_map


async def seed_school_defaults(school_id: str, db: AsyncSession) -> None:
    """
    Called after school creation. Creates:
    1. System roles with correct permissions
    2. Default leave types
    3. Default school settings
    4. Default grading scale
    5. Default fee/income/expense categories
    6. Default notification templates
    """
    role_repo = RoleRepository(db)
    # Ensure all platform permissions are in DB
    perm_map = await seed_platform_permissions(db)

    for role_def in SYSTEM_ROLES:
        existing = await role_repo.get_by_slug(role_def["slug"], school_id)
        if existing:
            continue
        role = await role_repo.create(
            school_id=school_id,
            data={
                "name": role_def["name"],
                "slug": role_def["slug"],
                "description": role_def["description"],
                "is_system": True,
                "is_active": True,
            },
        )
        # Assign permissions
        allowed_slugs = ROLE_PERMISSIONS.get(role_def["slug"], [])
        perm_ids = list(dict.fromkeys(perm_map[slug] for slug in allowed_slugs if slug in perm_map))
        await role_repo.assign_permissions(str(role.id), perm_ids)

    # ── Seed Default Document Templates ───────────────────────────────────
    for tpl in DEFAULT_DOCUMENT_TEMPLATES:
        existing = await db.execute(
            text(
                "SELECT id FROM document_templates "
                "WHERE school_id = :sid AND template_type = :ttype AND template_name = :tname"
            ),
            {"sid": school_id, "ttype": tpl["template_type"], "tname": tpl["template_name"]},
        )
        if existing.fetchone():
            continue
        await db.execute(
            text(
                "INSERT INTO document_templates "
                "(id, school_id, template_name, template_type, canvas_width_mm, canvas_height_mm, "
                "template_html, layout_json, is_default, is_active, created_at, updated_at) "
                "VALUES (:id, :sid, :tname, :ttype, :w, :h, :html, NULL, :is_def, true, "
                "NOW(), NOW())"
            ),
            {
                "id": str(uuid.uuid4()),
                "sid": school_id,
                "tname": tpl["template_name"],
                "ttype": tpl["template_type"],
                "w": tpl["canvas_width_mm"],
                "h": tpl["canvas_height_mm"],
                "html": tpl["template_html"],
                "is_def": tpl["is_default"],
            },
        )
    await db.commit()

    # ── Seed Default Notification Templates ───────────────────────────────
    for ntpl in DEFAULT_NOTIFICATION_TEMPLATES:
        existing = await db.execute(
            text(
                "SELECT id FROM notification_templates "
                "WHERE school_id = :sid AND event_trigger = :evt AND name = :name"
            ),
            {"sid": school_id, "evt": ntpl["event_trigger"], "name": ntpl["name"]},
        )
        if existing.fetchone():
            continue
        await db.execute(
            text(
                "INSERT INTO notification_templates "
                "(id, school_id, name, channels, event_trigger, subject, body_template, "
                "is_active, is_default, created_at, updated_at) "
                "VALUES (:id, :sid, :name, :ch, :evt, :subj, :body, "
                ":is_active, :is_def, NOW(), NOW())"
            ),
            {
                "id": str(uuid.uuid4()),
                "sid": school_id,
                "name": ntpl["name"],
                "ch": ntpl["channel"],
                "evt": ntpl["event_trigger"],
                "subj": ntpl.get("subject"),
                "body": ntpl["body_template"],
                "is_active": ntpl["is_active"],
                "is_def": ntpl["is_default"],
            },
        )
    await db.commit()

    # ── Seed Default Public Website Config (unpublished by default) ────────────
    from app.repositories.website_repository import WebsiteConfigRepository

    if await WebsiteConfigRepository(db).get_by_school(school_id) is None:
        await WebsiteConfigRepository(db).create_default(school_id)
        await db.commit()

