# Feature Prompt 03 — Roles & Permissions (RBAC)

## Round: 1 of 4 — Foundation
## Prerequisites: Prompts 01 + 02 complete (Infrastructure + Auth)

---

## Objective

Implement the full Role-Based Access Control system: 14 built-in system roles, 27-module permission registry, many-to-many role–permission assignments, user–role assignment, the `permission_required` dependency (already scaffolded in Prompt 02), and the frontend permission matrix UI at `/admin/roles`.

---

## 1. Database Models (`backend/app/models/rbac.py`)

```python
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, Enum as SAEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.models.base import Base, TimestampMixin
import enum

class PermissionModule(str, enum.Enum):
    DASHBOARD = "dashboard"
    SCHOOLS = "schools"
    USERS = "users"
    ROLES = "roles"
    ACADEMIC_YEARS = "academic_years"
    ADMISSIONS = "admissions"
    CLASSES = "classes"
    SUBJECTS = "subjects"
    TIMETABLE = "timetable"
    STAFF = "staff"
    LEAVES = "leaves"
    PAYROLL = "payroll"
    STUDENTS = "students"
    ATTENDANCE = "attendance"
    FEES = "fees"
    EXAMS = "exams"
    LIBRARY = "library"
    TRANSPORT = "transport"
    INVENTORY = "inventory"
    ACCOUNTING = "accounting"
    COMMUNICATION = "communication"
    CALENDAR = "calendar"
    HOMEWORK = "homework"
    PTM = "ptm"
    REPORTS = "reports"
    AUDIT_LOGS = "audit_logs"
    SETTINGS = "settings"

class PermissionAction(str, enum.Enum):
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    APPROVE = "approve"
    MANAGE = "manage"

class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # built-in: non-deletable
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("school_id", "slug", name="uq_roles_school_slug"),
    )

    role_permissions: Mapped[list["RolePermission"]] = relationship("RolePermission", back_populates="role")
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="role")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module: Mapped[PermissionModule] = mapped_column(SAEnum(PermissionModule), nullable=False)
    action: Mapped[PermissionAction] = mapped_column(SAEnum(PermissionAction), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)

    __table_args__ = (
        UniqueConstraint("module", "action", name="uq_permissions_module_action"),
    )

    role_permissions: Mapped[list["RolePermission"]] = relationship("RolePermission", back_populates="permission")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
    )

    role: Mapped[Role] = relationship("Role", back_populates="role_permissions")
    permission: Mapped[Permission] = relationship("Permission", back_populates="role_permissions")


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles"),
    )

    user: Mapped["User"] = relationship("User", back_populates="user_roles")
    role: Mapped[Role] = relationship("Role", back_populates="user_roles")
```

---

## 2. Alembic Migration

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    is_system BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_roles_school_slug UNIQUE (school_id, slug)
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description VARCHAR(300),
    CONSTRAINT uq_permissions_module_action UNIQUE (module, action)
);

CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    CONSTRAINT uq_role_permissions UNIQUE (role_id, permission_id)
);

CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    assigned_by UUID,
    assigned_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_user_roles UNIQUE (user_id, role_id)
);

CREATE INDEX ix_user_roles_user_id ON user_roles(user_id);
CREATE INDEX ix_user_roles_school_id ON user_roles(school_id);
CREATE INDEX ix_role_permissions_role_id ON role_permissions(role_id);
```

---

## 3. Seed Function: `backend/app/scripts/seed_data.py`

This function is called when a new school is created. It seeds all system roles, all permissions, and default role-permission assignments.

### 3a. System Roles (14 built-in roles, `is_system=True`)

| Slug | Name |
|------|------|
| `school_admin` | School Admin |
| `principal` | Principal |
| `vice_principal` | Vice Principal |
| `teacher` | Teacher |
| `class_teacher` | Class Teacher |
| `accountant` | Accountant |
| `librarian` | Librarian |
| `transport_manager` | Transport Manager |
| `inventory_manager` | Inventory Manager |
| `hr_manager` | HR Manager |
| `receptionist` | Receptionist |
| `parent` | Parent |
| `student` | Student |
| `counselor` | Counselor |

### 3b. All Permissions (27 modules × up to 7 actions = ~100 permissions)

Create a permission for every valid (module, action) combination. Not all combinations exist:
- `dashboard`: only `view`
- `reports`: `view`, `export`
- `audit_logs`: `view`, `export`
- `settings`: `view`, `update`, `manage`
- `attendance`: `view`, `create`, `update`, `delete`, `export`
- All other modules: `view`, `create`, `update`, `delete`, `export`, `approve`, `manage` where applicable

### 3c. Default Role-Permission Assignments

```
school_admin:
  - ALL permissions except super-admin-only ones

principal:
  - view/create/update on: students, staff, attendance, exams, classes, subjects, timetable, fees (view only), reports, audit_logs, calendar, communication, homework, ptm, leaves (approve), settings (view)

teacher / class_teacher:
  - attendance: view, create, update
  - students: view
  - exams: view, create, update (own exams only — enforced in service)
  - homework: view, create, update, delete
  - timetable: view
  - calendar: view
  - ptm: view, create, update
  - leaves: view, create (own)

accountant:
  - fees: view, create, update, export, approve
  - accounting: view, create, update, export
  - payroll: view, create, update, export
  - reports: view, export

librarian:
  - library: all actions

transport_manager:
  - transport: all actions

inventory_manager:
  - inventory: all actions

hr_manager:
  - staff: view, create, update, export
  - leaves: all actions
  - payroll: all actions

receptionist:
  - students: view
  - admissions: view, create, update
  - fees: view, create
  - communication: view, create

parent:
  - dashboard: view
  - attendance: view (own child)
  - fees: view (own child)
  - exams: view (own child)
  - library: view
  - transport: view
  - homework: view
  - ptm: view, create

student:
  - dashboard: view
  - attendance: view (own)
  - fees: view (own)
  - exams: view (own)
  - library: view
  - homework: view, create
  - timetable: view
  - calendar: view

counselor:
  - students: view
  - attendance: view
  - reports: view
```

---

## 4. Pydantic Schemas (`backend/app/schemas/rbac.py`)

```python
from pydantic import BaseModel
from uuid import UUID
from enum import Enum

class RoleCreate(BaseModel):
    name: str
    description: str | None = None

class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None

class RoleResponse(BaseModel):
    id: UUID
    schoolId: UUID
    name: str
    slug: str
    description: str | None
    isSystem: bool
    isActive: bool
    permissionCount: int = 0
    model_config = {"from_attributes": True}

class PermissionResponse(BaseModel):
    id: UUID
    module: str
    action: str
    description: str | None
    model_config = {"from_attributes": True}

class PermissionMatrixRow(BaseModel):
    module: str
    actions: dict[str, bool]  # {"view": True, "create": False, ...}

class UpdateRolePermissionsRequest(BaseModel):
    """List of permission IDs to assign to this role (replaces all current)."""
    permission_ids: list[UUID]

class AssignRoleRequest(BaseModel):
    user_id: UUID
    role_ids: list[UUID]
```

---

## 5. Repository (`backend/app/repositories/role_repository.py`)

```python
async def get_roles_for_school(db, school_id: UUID) -> list[Role]: ...
async def get_role_by_id(db, role_id: UUID, school_id: UUID) -> Role | None: ...
async def create_role(db, school_id: UUID, name: str, description: str) -> Role: ...
async def update_role(db, role: Role, data: dict) -> Role: ...
async def delete_role(db, role: Role) -> None:
    """Soft delete — is_active=False. Refuse if is_system=True."""
    ...
async def get_all_permissions(db) -> list[Permission]: ...
async def get_permissions_for_role(db, role_id: UUID) -> list[Permission]: ...
async def set_role_permissions(db, role_id: UUID, permission_ids: list[UUID]) -> None:
    """Replace all current role_permissions for this role."""
    ...
async def assign_roles_to_user(db, user_id: UUID, role_ids: list[UUID], school_id: UUID,
                               assigned_by: UUID) -> None: ...
async def get_roles_for_user(db, user_id: UUID) -> list[Role]: ...
async def clone_role(db, source_role_id: UUID, new_name: str, school_id: UUID) -> Role:
    """Clone a role with all its permissions."""
    ...
```

---

## 6. Service (`backend/app/services/role_service.py` + `seed_school_defaults`)

```python
async def seed_school_defaults(db: AsyncSession, school_id: UUID, created_by_id: UUID):
    """
    Called on every new school creation. Creates:
    1. All 14 system roles for this school
    2. Ensures all permissions exist (idempotently)
    3. Assigns default permissions to each role per the matrix above
    4. Creates default school settings (called from school_service)
    5. Creates default grading scale (CBSE 10-point)
    6. Creates default notification templates for all event triggers
    """
    ...

async def create_role(db, school_id, data: RoleCreate, current_user) -> Role:
    """Create a custom role. Slug = slugify(name). Audit log."""
    ...

async def update_role_permissions(db, role_id, school_id, permission_ids, current_user) -> None:
    """Replace permissions. Cannot modify system role permissions (raise 403). Audit log."""
    ...

async def clone_role(db, role_id, new_name, school_id, current_user) -> Role:
    """Deep clone: new role with same permissions."""
    ...

async def delete_role(db, role_id, school_id, current_user) -> None:
    """Soft delete. Refuse if is_system=True. Refuse if users have this role."""
    ...
```

---

## 7. API Endpoints (`backend/app/api/v1/endpoints/roles.py`)

```
GET    /roles                          → list all roles for school
POST   /roles                          → create custom role
GET    /roles/{role_id}                → get role detail with permissions
PUT    /roles/{role_id}                → update role name/description
DELETE /roles/{role_id}                → soft delete (refuse if system)
POST   /roles/{role_id}/clone          → clone role with permissions
GET    /roles/{role_id}/permissions    → get permission matrix for role
PUT    /roles/{role_id}/permissions    → bulk replace permissions
GET    /permissions                    → list all permission definitions
POST   /users/{user_id}/roles          → assign roles to user
GET    /users/{user_id}/roles          → get roles for user
```

All endpoints gated with `permission_required("roles", action)`.

---

## 8. Frontend: Types

```typescript
// frontend/src/types/index.ts (add these)

export interface Role {
  id: string;
  name: string;
  slug: string;
  description?: string;
  isSystem: boolean;
  isActive: boolean;
  permissionCount: number;
}

export interface Permission {
  id: string;
  module: string;
  action: string;
  description?: string;
}

export interface PermissionMatrix {
  [module: string]: {
    [action: string]: { permissionId: string; granted: boolean };
  };
}
```

---

## 9. Frontend: API Layer (`frontend/src/api/roles.ts`)

```typescript
import api from './axios';
import type { Role, Permission } from '@/types';

export const getRolesApi = async () => {
  const res = await api.get<{ data: Role[] }>('/roles');
  return res.data.data;
};

export const createRoleApi = async (data: { name: string; description?: string }) => {
  const res = await api.post<{ data: Role }>('/roles', data);
  return res.data.data;
};

export const updateRoleApi = async (id: string, data: Partial<Role>) => {
  const res = await api.put<{ data: Role }>(`/roles/${id}`, data);
  return res.data.data;
};

export const deleteRoleApi = async (id: string) => api.delete(`/roles/${id}`);

export const cloneRoleApi = async (id: string, newName: string) =>
  api.post(`/roles/${id}/clone`, { name: newName });

export const getRolePermissionsApi = async (id: string) => {
  const res = await api.get<{ data: Permission[] }>(`/roles/${id}/permissions`);
  return res.data.data;
};

export const setRolePermissionsApi = async (id: string, permissionIds: string[]) =>
  api.put(`/roles/${id}/permissions`, { permission_ids: permissionIds });

export const getAllPermissionsApi = async () => {
  const res = await api.get<{ data: Permission[] }>('/permissions');
  return res.data.data;
};
```

---

## 10. Frontend: Roles Page (`frontend/src/pages/admin/RolesPage.tsx`)

Build a full roles management page at route `/admin/roles`:

### Layout
- **PageHeader**: "Roles & Permissions" + "New Role" button (gated with `permission_required("roles","create")`)
- **Roles Table**: columns: Name, Type (System/Custom badge), Permissions Count, Status, Actions (Edit/Clone/Delete)
  - System roles: Clone and Edit only (no Delete)
  - Custom roles: Edit, Clone, Delete
- **"Edit Permissions" drawer/modal**: opens when clicking a role
  - Shows full permission matrix: rows = 27 modules, columns = 7 actions
  - Each cell is a checkbox (enabled/disabled based on whether that module+action has a permission record)
  - "Select All" checkbox per row (module) and per column (action)
  - Save triggers `setRolePermissionsApi` with all checked permission IDs
  - Optimistic update with error rollback

### "New Role" Dialog
- Name input
- Description input
- Submit → `createRoleApi`

### "Clone Role" Dialog
- New name input for the cloned role

---

## 11. Frontend: `usePermission` hook update

The `usePermission` hook from Prompt 01 is already correct. Ensure it reads from `useAuthStore().permissions` (array of `"module:action"` strings).

---

## 12. Sidebar Navigation

Add to `frontend/src/components/layout/Sidebar.tsx`:
- Under "Administration" section: `Roles & Permissions` → `/admin/roles` (visible to: `school_admin`, `principal`)

---

## Verification Checklist

- [ ] `GET /api/v1/permissions` returns all ~100 permission records
- [ ] `GET /api/v1/roles` returns 14 system roles for a school (after `seed_school_defaults`)
- [ ] Creating a new school triggers `seed_school_defaults` (14 roles + all permissions created)
- [ ] `PUT /roles/{id}/permissions` correctly replaces the role's permission assignments
- [ ] System roles cannot be deleted (returns 403)
- [ ] `permission_required("students","create")` returns 403 for a role without that permission
- [ ] Super admin bypasses all permission checks
- [ ] `GET /auth/me` returns `permissions: ["students:view", "fees:create", ...]`
- [ ] Frontend permission matrix grid renders all 27 × 7 cells
- [ ] Toggling a checkbox and saving correctly updates the role's permissions
- [ ] `<PermissionGuard module="roles" action="create">` hides "New Role" button for unauthorized users
