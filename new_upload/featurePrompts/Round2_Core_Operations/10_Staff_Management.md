# Feature Prompt 10 — Staff Management

## Round: 2 of 4 — Core Operations
## Prerequisites: Prompts 01–09 complete

---

## Objective

Implement full staff member management: profile with auto-generated employee ID, departments, designations, photo upload, qualification records, document management, staff portal, and ID card generation. Leave and Payroll are covered in separate prompts (11 & 15).

---

## 1. Database Models (`backend/app/models/staff.py`)

```python
import uuid
from datetime import date
from sqlalchemy import String, Boolean, Date, Integer, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
import enum

class EmploymentType(str, enum.Enum):
    PERMANENT = "permanent"
    CONTRACT = "contract"
    PART_TIME = "part_time"
    DAILY_WAGE = "daily_wage"

class StaffStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    RESIGNED = "resigned"

class Department(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    head_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=True)   # NOTE: head_id (NOT hod_id)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Designation(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "designations"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("departments.id"), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1)  # hierarchy level
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Staff(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "staff"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=True)
    employee_id: Mapped[str] = mapped_column(String(50), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("departments.id"), nullable=True)
    designation_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("designations.id"), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    blood_group: Mapped[str | None] = mapped_column(String(5), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[EmploymentType] = mapped_column(String(20),
        default=EmploymentType.PERMANENT)
    joining_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    leaving_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[StaffStatus] = mapped_column(String(20), default=StaffStatus.ACTIVE)
    qualification: Mapped[str | None] = mapped_column(String(200), nullable=True)
    experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Salary
    monthly_salary_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Bank details
    bank_account_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    bank_ifsc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Govt IDs
    pan_number: Mapped[str | None] = mapped_column(String(15), nullable=True)
    pf_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    esi_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    documents: Mapped[list["StaffDocument"]] = relationship("StaffDocument", back_populates="staff")

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("school_id", "employee_id", name="uq_staff_employee_id"),
    )


class StaffDocument(Base, TimestampMixin):
    __tablename__ = "staff_documents"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    staff: Mapped[Staff] = relationship("Staff", back_populates="documents")
```

---

## 2. Alembic Migration

```sql
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    head_id UUID REFERENCES users(id),   -- head_id (NOT hod_id)
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE designations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    department_id UUID REFERENCES departments(id),
    level INTEGER DEFAULT 1 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    employee_id VARCHAR(50) NOT NULL,
    department_id UUID REFERENCES departments(id),
    designation_id UUID REFERENCES designations(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    blood_group VARCHAR(5),
    photo_url VARCHAR(500),
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    employment_type VARCHAR(20) DEFAULT 'permanent' NOT NULL,
    joining_date DATE,
    leaving_date DATE,
    status VARCHAR(20) DEFAULT 'active' NOT NULL,
    qualification VARCHAR(200),
    experience_years FLOAT,
    monthly_salary_paise INTEGER DEFAULT 0 NOT NULL,
    bank_account_number VARCHAR(30),
    bank_ifsc VARCHAR(20),
    bank_name VARCHAR(100),
    pan_number VARCHAR(15),
    pf_number VARCHAR(30),
    esi_number VARCHAR(30),
    emergency_contact_name VARCHAR(200),
    emergency_contact_phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_staff_employee_id UNIQUE (school_id, employee_id)
);

CREATE INDEX ix_staff_school_id ON staff(school_id);
CREATE INDEX ix_staff_school_status ON staff(school_id, status);

CREATE TABLE staff_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    file_name VARCHAR(200),
    uploaded_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
```

---

## 3. Employee ID Generation (`backend/app/utils/employee_id.py`)

```python
async def generate_employee_id(db, redis, school_id: UUID) -> str:
    """
    Atomically increment employee_id_last_seq in school_settings using SELECT FOR UPDATE.
    Format: EMP-{YEAR}-{SEQ:04d}
    """
    # Read and increment sequence with FOR UPDATE
    ...
```

---

## 4. Pydantic Schemas

```python
class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None
    headId: UUID | None = None

class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    headId: UUID | None
    headName: str | None = None
    staffCount: int = 0
    model_config = {"from_attributes": True}

class DesignationCreate(BaseModel):
    name: str
    departmentId: UUID | None = None
    level: int = 1

class StaffCreate(BaseModel):
    firstName: str
    lastName: str
    departmentId: UUID | None = None
    designationId: UUID | None = None
    gender: str | None = None
    dateOfBirth: date | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    employmentType: str = "permanent"
    joiningDate: date | None = None
    qualification: str | None = None
    experienceYears: float | None = None
    monthlySalaryPaise: int = 0
    bankAccountNumber: str | None = None
    bankIfsc: str | None = None
    bankName: str | None = None
    panNumber: str | None = None
    emergencyContactName: str | None = None
    emergencyContactPhone: str | None = None
    createUserAccount: bool = True  # auto-create login account
    assignRoles: list[UUID] = []    # role IDs to assign

class StaffResponse(BaseModel):
    id: UUID
    employeeId: str
    firstName: str
    lastName: str
    fullName: str
    photoUrl: str | None
    departmentName: str | None
    designationName: str | None
    employmentType: str
    status: str
    phone: str | None
    email: str | None
    joiningDate: date | None
    isActive: bool
    model_config = {"from_attributes": True}

class StaffListFilter(BaseModel):
    departmentId: UUID | None = None
    designationId: UUID | None = None
    employmentType: str | None = None
    status: str | None = None
    search: str | None = None
```

---

## 5. Service (`backend/app/services/staff_service.py`)

```python
async def create_staff(db, redis, school_id, data: StaffCreate, current_user) -> Staff:
    """
    1. Generate employee ID.
    2. Create Staff record.
    3. If createUserAccount=True: create User(username=email or phone, role=assigned_roles).
    4. Link User to Staff.
    5. Enqueue welcome email.
    6. Audit log.
    """
    ...

async def update_staff(db, staff_id, school_id, data: dict, current_user) -> Staff:
    """Update staff profile. Audit log."""
    ...

async def upload_photo(db, staff_id, school_id, file: UploadFile, current_user) -> str:
    """Save to uploads/staff/{id}/photo.jpg. Update staff.photo_url."""
    ...

async def terminate_staff(db, staff_id, school_id, leaving_date: date, current_user) -> Staff:
    """Set status=terminated, leaving_date. Soft delete user account."""
    ...

async def get_staff_list(db, school_id, filters: StaffListFilter, page, page_size) -> tuple:
    """Return (staff_list, pagination) with joinedload department/designation."""
    ...

async def generate_staff_id_card_pdf(db, staff_id, school_id) -> bytes:
    """Render staff ID card template with WeasyPrint."""
    ...
```

---

## 6. API Endpoints

```
# Departments
GET    /departments                          → list departments                [staff:view]
POST   /departments                          → create department               [staff:create]
PUT    /departments/{id}                     → update department               [staff:update]
DELETE /departments/{id}                     → soft delete                     [staff:delete]

# Designations
GET    /designations?department_id=          → list designations               [staff:view]
POST   /designations                         → create designation              [staff:create]
PUT    /designations/{id}                    → update                          [staff:update]

# Staff
GET    /staff                                → paginated list with filters     [staff:view]
POST   /staff                                → create staff member             [staff:create]
GET    /staff/{id}                           → staff detail                    [staff:view]
PUT    /staff/{id}                           → update staff                    [staff:update]
POST   /staff/{id}/photo                     → upload photo                    [staff:update]
POST   /staff/{id}/terminate                 → terminate staff member          [staff:update]
GET    /staff/{id}/id-card                   → download ID card PDF            [staff:export]
GET    /staff/stats                          → summary counts                  [staff:view]

# Documents
GET    /staff/{id}/documents                 → list documents                  [staff:view]
POST   /staff/{id}/documents                 → upload document                 [staff:update]
DELETE /staff/{id}/documents/{did}           → remove document                 [staff:update]

# Bulk
GET    /staff/export                         → Excel export                    [staff:export]
```

---

## 7. Frontend: Staff Pages

### Staff List Page (`/staff`)
- **PageHeader**: "Staff" + "Add Staff" + "Export Excel" buttons
- **Filter bar**: Department, Designation, Employment Type, Status, Search
- **TanStack Table**: Employee ID | Photo | Name | Department | Designation | Type | Status | Actions
- **Actions**: View Profile, Edit, Generate ID Card, Terminate

### Staff Detail Page (`/staff/:id`)
5-tab layout:
1. **Profile**: All personal + professional fields, photo upload
2. **Documents**: Document list + upload
3. **Leave**: Leave balance + history (links to Leave module)
4. **Payroll**: Payslip history (links to Payroll module)
5. **Timetable**: Class schedule for teacher staff

### Staff Registration Form
Multi-step:
1. Personal Info
2. Job Details (department, designation, employment type, joining date)
3. Salary & Bank
4. Documents + Account Setup

---

## 8. Sidebar Navigation

Add under "Staff" section:
- `All Staff` → `/staff`
- `Departments` → `/departments`

---

## Verification Checklist

- [ ] `POST /staff` generates unique employee ID (`EMP-2025-0001`)
- [ ] Duplicate employee ID in same school returns 409
- [ ] Staff photo upload saves and links correctly
- [ ] Terminating staff sets `status=terminated` and deactivates user account
- [ ] `GET /staff` filter by department/designation works
- [ ] Department CRUD with head assignment works
- [ ] Staff ID card PDF generated from template
- [ ] `GET /staff/export` returns Excel file
- [ ] Staff detail page shows all 5 tabs
- [ ] `createUserAccount=True` creates a `users` record with assigned roles
