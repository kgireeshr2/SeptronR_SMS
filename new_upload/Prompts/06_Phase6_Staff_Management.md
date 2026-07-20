# PHASE 6 — STAFF MANAGEMENT

## Pre-Requisite
Phases 1–4 complete. Users/roles system working. Classes and sections exist.

## Objective
Complete staff lifecycle: employee registration, profile, department/designation management, leave management, payroll basic, staff portal login, and document management.

---

## 6.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 9: Staff
departments (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, description TEXT,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, name)
)

designations (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, grade_pay BIGINT DEFAULT 0,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, name)
)

staff (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    employee_id VARCHAR(50), user_id UUID FK→users UNIQUE (nullable),
    department_id UUID FK→departments (nullable),
    designation_id UUID FK→designations (nullable),
    first_name VARCHAR(100) NOT NULL, last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE, gender VARCHAR(10),
    blood_group VARCHAR(5), religion VARCHAR(50),
    nationality VARCHAR(60) DEFAULT 'Indian',
    photo_url TEXT, address TEXT,
    bank_account_no VARCHAR(30), ifsc_code VARCHAR(20),
    emergency_contact JSONB,   -- {name, phone, relation}
    qualifications JSONB,      -- [{degree, institution, year}]
    joining_date DATE,
    employment_type VARCHAR(20) DEFAULT 'permanent',
        -- permanent|contractual|part_time|visiting
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    deleted_at TIMESTAMPTZ, deleted_by UUID FK→users,
    UNIQUE(school_id, employee_id)
)
-- NOTE: staff table does NOT have separate pan_number, pf_number, esi_number, caste,
-- bank_name, aadhaar_number, experience_years, leaving_date, status enum.
-- Store PAN/PF/ESI in staff_documents; leaving_date tracked via terminated_at audit log.

staff_documents (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    staff_id UUID FK→staff ON DELETE CASCADE,
    doc_type VARCHAR(60),   -- NOTE: 'doc_type' not 'document_type'
        -- CV|Degree|Aadhaar|PAN|ExperienceLetter|Other
    file_url TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
)

leave_types (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, days_allowed SMALLINT NOT NULL,
    is_paid BOOL DEFAULT TRUE, carry_forward BOOL DEFAULT FALSE,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, name)
)

-- ⚠️ TABLE NAME: staff_leave_balances (NOT leave_allocations)
staff_leave_balances (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    staff_id UUID FK→staff ON DELETE CASCADE,
    leave_type_id UUID FK→leave_types,
    academic_year_id UUID FK→academic_years,
    total_days SMALLINT NOT NULL, used_days SMALLINT DEFAULT 0,
    remaining_days SMALLINT GENERATED ALWAYS AS (total_days - used_days) STORED,
    UNIQUE(staff_id, leave_type_id, academic_year_id)
)

-- ⚠️ TABLE NAME: staff_leaves (NOT leave_applications)
staff_leaves (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    staff_id UUID FK→staff ON DELETE CASCADE,
    leave_type_id UUID FK→leave_types,
    from_date DATE NOT NULL, to_date DATE NOT NULL,
    total_days SMALLINT NOT NULL,
    reason TEXT, status leave_status DEFAULT 'pending',
        -- ENUM: pending|approved|rejected|cancelled
    substitute_staff_id UUID FK→staff (nullable),
    approved_by UUID FK→users (nullable), approved_at TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at, updated_at
)

-- ⚠️ PAYROLL STRUCTURE: Uses JSONB for allowances/deductions (NOT separate columns for HRA/DA/TA)
staff_payroll (
    id UUID PK, staff_id UUID FK→staff, school_id UUID FK→schools ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    month SMALLINT NOT NULL, year SMALLINT NOT NULL,   -- 1-12 / calendar year
    basic_salary BIGINT DEFAULT 0,                     -- stored in paise
    allowances JSONB DEFAULT '{}',   -- {hra: N, da: N, ta: N, other: N}
    deductions JSONB DEFAULT '{}',   -- {pf: N, esi: N, tds: N, loan: N, other: N}
    gross_salary BIGINT GENERATED ALWAYS AS (basic_salary + COALESCE(allowances totals)) STORED,
    net_salary BIGINT,               -- computed and stored at generation time
    working_days SMALLINT, days_present SMALLINT,
    is_paid BOOL DEFAULT FALSE,      -- NOTE: Boolean, not a status enum
    payment_date DATE, payment_mode VARCHAR(30),
    payment_reference VARCHAR(100), remarks TEXT,
    generated_by UUID FK→users,
    created_at, updated_at,
    UNIQUE(staff_id, month, year)
)
-- NOTE: payroll does NOT have a 'status' enum (draft|approved|paid).
-- Use is_paid=FALSE for draft/approved state. Add a separate 'is_approved' column via migration
-- if draft→approve→paid workflow is needed. OR add status enum via Alembic migration.
```

> **Schema note — payroll allowances/deductions format:**
> ```python
> allowances = {"hra": 500000, "da": 200000, "ta": 100000, "other": 0}   # paise
> deductions  = {"pf": 180000, "esi": 7500, "tds": 0, "loan": 0, "other": 0}
> ```
> Both stored as JSONB. Access as `payroll.allowances["hra"]` in Python.

---

## 6.2 SQLAlchemy Models (`backend/app/models/staff.py`)

```python
class LeaveStatus(str, PyEnum):
    pending = "pending"; approved = "approved"; rejected = "rejected"; cancelled = "cancelled"

# NOTE: No PayrollStatus enum in schema — payroll uses is_paid: bool
# Add 'is_approved: bool = False' column via migration if draft→approved workflow is needed

class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class Designation(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class Staff(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class LeaveType(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class StaffLeaveBalance(Base, UUIDPrimaryKeyMixin): ...   # table: staff_leave_balances
class StaffLeave(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...  # table: staff_leaves
class StaffPayroll(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    # allowances: Mapped[dict] = mapped_column(JSONB, default={})
    # deductions: Mapped[dict] = mapped_column(JSONB, default={})
    # is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    ...
```

---

## 6.3 Pydantic Schemas

```python
class DepartmentCreate(BaseModel):
    name: str; description: Optional[str]

class DesignationCreate(BaseModel):
    name: str; grade_pay: Optional[int] = 0

class StaffCreate(BaseModel):
    first_name: str; last_name: str
    date_of_birth: Optional[date]
    gender: Optional[str]
    employment_type: str = "permanent"
    department_id: Optional[UUID]
    designation_id: Optional[UUID]
    joining_date: date
    bank_account_no: Optional[str]     # field name in DB
    ifsc_code: Optional[str]           # field name in DB (not bank_ifsc)
    address: Optional[str]
    emergency_contact: Optional[dict] = None  # {name, phone, relation} stored as JSONB
    qualifications: Optional[list] = None     # [{degree, institution, year}] as JSONB
    # Login is auto-created at create time
    email: EmailStr       # becomes username
    phone: str
    role_ids: List[UUID]  # assign roles immediately

class StaffResponse(BaseModel):
    id: UUID
    employee_id: str
    user_id: UUID
    full_name: str   # f"{first_name} {last_name}"
    email: str; phone: str
    department_name: Optional[str]; designation_name: Optional[str]
    employment_type: str; joining_date: date; status: str
    photo_url: Optional[str]
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class LeaveApplicationCreate(BaseModel):
    leave_type_id: UUID
    from_date: date
    to_date: date
    reason: str
    substitute_teacher_id: Optional[UUID]

class LeaveApplicationReview(BaseModel):
    status: Literal["approved", "rejected"]
    rejection_reason: Optional[str]

class PayrollGenerateRequest(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int
    academic_year_id: UUID
    staff_ids: Optional[List[UUID]] = None  # None = all active staff

class PayrollEntry(BaseModel):
    staff_id: UUID
    basic_salary: int   # paise
    # JSONB fields — match DB structure exactly:
    allowances: dict = Field(default_factory=lambda: {"hra": 0, "da": 0, "ta": 0, "other": 0})
    deductions: dict = Field(default_factory=lambda: {"pf": 0, "esi": 0, "tds": 0, "loan": 0, "other": 0})
    working_days: Optional[int]; days_present: Optional[int]
    is_paid: bool = False
    payment_mode: Optional[str]; payment_reference: Optional[str]; remarks: Optional[str]
```

---

## 6.4 Employee ID Generation

```python
async def generate_employee_id(school_id: str, db: AsyncSession) -> str:
    """
    Format: EMP-{4-digit-school-seq}
    Or custom format from school settings: staff_id_prefix
    """
```

---

## 6.5 Repository Layer

### `backend/app/repositories/staff_repository.py`
```python
class StaffRepository:
    async def create(self, school_id: str, data: dict) -> Staff: ...
    async def get_by_id(self, staff_id: str) -> Optional[Staff]: ...
    async def get_by_user_id(self, user_id: str) -> Optional[Staff]: ...
    async def get_by_employee_id(self, school_id: str, emp_id: str) -> Optional[Staff]: ...
    async def list(self, school_id: str, filters: dict, page: int, page_size: int) -> tuple: ...
    async def update(self, staff_id: str, data: dict) -> Staff: ...
    async def soft_delete(self, staff_id: str, deleted_by: str) -> None: ...
    async def count_by_department(self, school_id: str) -> List[dict]: ...
    async def count_by_designation(self, school_id: str) -> List[dict]: ...

class LeaveRepository:
    # ⚠️ Uses staff_leave_balances table (not leave_allocations)
    async def get_balance(self, staff_id: str, leave_type_id: str, year_id: str) -> Optional[StaffLeaveBalance]: ...
    async def upsert_balance(self, data: dict) -> StaffLeaveBalance: ...
    # ⚠️ Uses staff_leaves table (not leave_applications)
    async def apply_leave(self, data: dict) -> StaffLeave: ...
    async def list_leaves(self, school_id: str, filters: dict, page: int, page_size: int) -> tuple: ...
    async def review(self, leave_id: str, data: dict) -> StaffLeave: ...
    async def deduct_balance(self, staff_id: str, leave_type_id: str, year_id: str, days: int) -> None: ...

class PayrollRepository:
    async def generate_for_month(self, school_id: str, month: int, year: int, year_id: str, staff_ids: Optional[list]) -> List[StaffPayroll]: ...
    async def get_by_staff_month(self, staff_id: str, month: int, year: int) -> Optional[StaffPayroll]: ...
    async def bulk_update(self, payroll_ids: List[str], data: dict) -> int: ...
    async def approve(self, payroll_id: str, approved_by: str) -> StaffPayroll: ...
    async def mark_paid(self, payroll_ids: List[str]) -> int: ...
```

---

## 6.6 Service Layer

### `backend/app/services/staff_service.py`

```python
async def create_staff(school_id: str, data: StaffCreate, created_by: str) -> Staff:
    """
    1. Generate employee_id
    2. Create User(email, phone, is_active=True) with temp password
    3. Assign role_ids to user
    4. Create Staff record linked to user
    5. Allocate leave for current academic year (all active leave types)
    6. Send welcome email/SMS with temp password
    """

async def terminate_staff(staff_id: str, leaving_date: date, reason: str, terminated_by: str):
    """
    1. Update staff: status=terminated, leaving_date, is_active=False
    2. Deactivate user account (is_active=False)
    3. Cancel pending leave applications
    4. Log audit
    """

async def process_leave_application(application_id: str, reviewer_id: str, data: LeaveApplicationReview):
    """
    1. Load application + allocation
    2. If approved: deduct days from allocation, send approval notification
    3. If rejected: send rejection notification with reason
    4. Update application status
    """

async def generate_monthly_payroll(school_id: str, data: PayrollGenerateRequest, generated_by: str) -> dict:
    """
    1. Load all active staff (or specific staff_ids)
    2. For each staff: calculate based on attendance for month, leave deductions
    3. Compute gross = basic + hra + da + ta + other_allowances
    4. Compute net = gross - pf - esi - tds - other_deductions
    5. Upsert StaffPayroll records (status=draft)
    6. Return {generated: N, already_exists: M}
    """

async def approve_payroll(payroll_ids: List[str], approved_by: str) -> int: ...
async def mark_payroll_paid(payroll_ids: List[str]) -> int: ...
async def get_payroll_slip_pdf(payroll_id: str) -> bytes:
    """Jinja2 + WeasyPrint payroll slip."""
```

---

## 6.7 API Endpoints

### Department & Designation
```
GET  /api/v1/departments              → list [staff:view]
POST /api/v1/departments              → create [staff:manage]
PUT  /api/v1/departments/{id}         → update
DELETE /api/v1/departments/{id}       → delete

GET  /api/v1/designations             → list [staff:view]
POST /api/v1/designations             → create [staff:manage]
PUT  /api/v1/designations/{id}        → update
DELETE /api/v1/designations/{id}      → delete
```

### Staff CRUD
```
GET    /api/v1/staff                  → list (filter: dept, designation, status, type, search) [staff:view]
POST   /api/v1/staff                  → create [staff:create]
GET    /api/v1/staff/{id}             → get full profile [staff:view]
PUT    /api/v1/staff/{id}             → update profile [staff:update]
DELETE /api/v1/staff/{id}             → soft delete [staff:delete]
POST   /api/v1/staff/{id}/photo       → upload photo [staff:update]
POST   /api/v1/staff/{id}/documents   → upload document
DELETE /api/v1/staff/{id}/documents/{did} → delete
POST   /api/v1/staff/{id}/terminate   → terminate staff [staff:manage]
GET    /api/v1/staff/export           → Excel export [staff:export]
POST   /api/v1/staff/bulk-import      → Excel import [staff:create]
GET    /api/v1/staff/stats            → counts by dept/designation [staff:view]
```

### Leave Management
```
GET  /api/v1/leave-types              → list leave types [leave:view]
POST /api/v1/leave-types              → create leave type [leave:manage]
PUT  /api/v1/leave-types/{id}         → update
DELETE /api/v1/leave-types/{id}       → delete

GET  /api/v1/leaves                   → list all applications (admin) [leave:view]
GET  /api/v1/leaves/my                → staff's own applications (current user)
POST /api/v1/leaves                   → apply for leave
GET  /api/v1/leaves/{id}              → get application detail
PUT  /api/v1/leaves/{id}/review       → approve/reject [leave:approve]
DELETE /api/v1/leaves/{id}            → cancel (only pending, own)

GET  /api/v1/leaves/balance/{staff_id}         → leave balance for staff
GET  /api/v1/leaves/calendar                   → all approved leaves in date range (for admin calendar)
GET  /api/v1/leaves/stats                      → leave stats (pending count, absent today)
```

### Payroll
```
GET  /api/v1/payroll                  → list payroll records (filter: month, year, status) [payroll:view]
POST /api/v1/payroll/generate         → generate for month [payroll:generate]
GET  /api/v1/payroll/{id}             → single payroll record
PUT  /api/v1/payroll/{id}             → update (only in draft status) [payroll:update]
POST /api/v1/payroll/approve          → bulk approve (ids in body) [payroll:approve]
POST /api/v1/payroll/mark-paid        → mark as paid (ids in body) [payroll:approve]
GET  /api/v1/payroll/{id}/slip        → PDF payroll slip [payroll:view]
GET  /api/v1/payroll/export           → Excel export for month [payroll:export]
```

---

## 6.8 Frontend Pages

### `/admin/staff` Page (Permission: `staff:view`)
- Filter: Department, Designation, Employment Type, Status, Search
- Table: Employee ID, Photo, Name, Department, Designation, Email/Phone, Joining Date, Status, Actions
- Export, Bulk Import buttons

### `/admin/staff/new` & `/admin/staff/:id` Pages
Tabs: Profile | Documents | Leave | Payroll | Timetable

**Profile Tab:** Personal info form, Bank details section, Emergency contact, Professional info
**Documents Tab:** Upload/view/delete documents (CV, degree certificates, aadhaar, etc.)
**Leave Tab:** Leave balance table + leave history table
**Payroll Tab:** Month selector → show payroll details + download slip

### `/admin/leave` Page (Permission: `leave:view`)
- Tabs: Pending Requests | All Applications | Leave Calendar
- Pending: actionable table with Approve/Reject buttons
- Calendar: monthly view, color-coded by leave type, hover shows staff name + leave type

### `/admin/payroll` Page (Permission: `payroll:view`)
- Month/Year picker → "Generate Payroll" button
- Table: Staff Name, Dept, Days Present/Absent, Gross, Deductions, Net, Status, Actions
- Inline edit of payroll details (draft only)
- Bulk approve, Bulk mark paid

### Staff Self-Service (via `/staff/` routes)
- `/staff/profile` → view profile, request changes
- `/staff/leave` → my leave balance + apply + history
- `/staff/payslips` → download monthly payslips
- `/staff/timetable` → my teaching schedule

### `frontend/src/api/staff.ts`
```typescript
export const staffApi = {
  list: (params: StaffListParams) => api.get('/staff', { params }),
  get: (id: string) => api.get(`/staff/${id}`),
  create: (data: StaffCreate) => api.post('/staff', data),
  update: (id: string, data: StaffUpdate) => api.put(`/staff/${id}`, data),
  terminate: (id: string, data: TerminateRequest) => api.post(`/staff/${id}/terminate`, data),
  uploadPhoto: (id: string, file: File) => { /* multipart */ },
  export: (params: StaffListParams) => api.get('/staff/export', { responseType: 'blob', params }),
  bulkImport: (file: File) => { /* multipart */ },
  stats: () => api.get('/staff/stats'),
};

export const leaveApi = {
  listTypes: () => api.get('/leave-types'),
  apply: (data: LeaveApplicationCreate) => api.post('/leaves', data),
  myLeaves: () => api.get('/leaves/my'),
  review: (id: string, data: LeaveApplicationReview) => api.put(`/leaves/${id}/review`, data),
  balance: (staffId: string, yearId: string) => api.get(`/leaves/balance/${staffId}?year_id=${yearId}`),
};

export const payrollApi = {
  list: (params: PayrollListParams) => api.get('/payroll', { params }),
  generate: (data: PayrollGenerateRequest) => api.post('/payroll/generate', data),
  update: (id: string, data: Partial<PayrollEntry>) => api.put(`/payroll/${id}`, data),
  approve: (ids: string[]) => api.post('/payroll/approve', { ids }),
  markPaid: (ids: string[]) => api.post('/payroll/mark-paid', { ids }),
  getSlip: (id: string) => api.get(`/payroll/${id}/slip`, { responseType: 'blob' }),
};
```

---

## 6.9 Celery Tasks

```python
@celery.task(queue="emails")
def send_staff_welcome_email(email: str, employee_id: str, temp_password: str, school_name: str): ...

@celery.task(queue="sms")
def send_leave_decision_sms(phone: str, staff_name: str, status: str, from_date: str, to_date: str): ...

@celery.task(queue="emails")
def send_payslip_email(email: str, payroll_id: str, month_year: str): ...
```

---

## 6.10 Tests

```python
async def test_create_staff_creates_user_account(): ...
async def test_employee_id_sequential(): ...
async def test_leave_application_deducts_balance_on_approval(): ...
async def test_leave_balance_insufficient_returns_422(): ...
async def test_payroll_generate_prevents_duplicate_month(): ...    # UNIQUE(staff_id, month, year)
async def test_payroll_draft_can_be_edited(): ...
async def test_payroll_approved_cannot_be_edited(): ...
async def test_terminate_staff_deactivates_user(): ...
```

---

## 6.11 Deliverables Checklist

- [ ] Department and Designation CRUD
- [ ] Staff registration creates user account with auto-generated employee_id
- [ ] Leave types CRUD, leave allocation per academic year
- [ ] Leave application → approval flow with balance deduction
- [ ] Leave calendar view for admin
- [ ] Payroll generation for a month (attendance-based)
- [ ] Payroll edit → approve → mark paid workflow
- [ ] Payroll slip PDF via WeasyPrint
- [ ] Staff self-service routes with appropriate role restrictions
- [ ] Staff profile with all tabs
- [ ] Bulk Excel import for staff
- [ ] Excel export of staff list
- [ ] Photo upload for staff
- [ ] Staff termination flow + user deactivation
- [ ] Payroll export to Excel
