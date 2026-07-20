# Feature Prompt 15 — Payroll

## Round: 3 of 4 — Academic & Financial
## Prerequisites: Prompts 10 (Staff Management), 11 (Leave Management), 13 (Staff Attendance)

---

## Objective

Implement monthly staff payroll generation with configurable salary components (allowances, deductions), attendance-based calculation, leave deduction (LWP), payslip PDF generation, and payroll history tracking.

---

## 1. Database Models (`backend/app/models/payroll.py`)

```python
import uuid
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
import enum

class PayrollStatus(str, enum.Enum):
    DRAFT = "draft"
    FINALIZED = "finalized"
    PAID = "paid"

class SalaryComponent(Base, TimestampMixin):
    """Reusable allowance/deduction components."""
    __tablename__ = "salary_components"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    component_type: Mapped[str] = mapped_column(String(20), nullable=False)  # allowance / deduction
    is_percentage: Mapped[bool] = mapped_column(Boolean, default=False)
    value: Mapped[int] = mapped_column(Integer, default=0)  # paise or percentage * 100
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StaffPayroll(Base, TimestampMixin):
    """Monthly payroll record per staff."""
    __tablename__ = "staff_payroll"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)   # 1–12
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    working_days: Mapped[int] = mapped_column(Integer, default=26)
    present_days: Mapped[int] = mapped_column(Integer, default=0)
    lwp_days: Mapped[int] = mapped_column(Integer, default=0)       # Leave Without Pay days
    basic_salary_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    allowances: Mapped[dict] = mapped_column(JSONB, default={})     # {component_name: amount_paise}
    deductions: Mapped[dict] = mapped_column(JSONB, default={})     # {component_name: amount_paise}
    gross_salary_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    total_deductions_paise: Mapped[int] = mapped_column(Integer, default=0)
    net_salary_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PayrollStatus] = mapped_column(String(20), default=PayrollStatus.DRAFT)
    payment_date: Mapped[str | None] = mapped_column(nullable=True)  # date when paid
    payment_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    finalized_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("staff_id", "month", "year", name="uq_staff_payroll_month"),
    )
```

---

## 2. Alembic Migration

```sql
CREATE TABLE salary_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    component_type VARCHAR(20) NOT NULL,  -- allowance / deduction
    is_percentage BOOLEAN DEFAULT FALSE NOT NULL,
    value INTEGER DEFAULT 0 NOT NULL,     -- paise or pct*100
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE staff_payroll (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    working_days INTEGER DEFAULT 26 NOT NULL,
    present_days INTEGER DEFAULT 0 NOT NULL,
    lwp_days INTEGER DEFAULT 0 NOT NULL,
    basic_salary_paise INTEGER NOT NULL,
    allowances JSONB DEFAULT '{}' NOT NULL,
    deductions JSONB DEFAULT '{}' NOT NULL,
    gross_salary_paise INTEGER NOT NULL,
    total_deductions_paise INTEGER DEFAULT 0 NOT NULL,
    net_salary_paise INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'draft' NOT NULL,
    payment_date DATE,
    payment_mode VARCHAR(20),
    remarks TEXT,
    finalized_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_staff_payroll_month UNIQUE (staff_id, month, year)
);

CREATE INDEX ix_staff_payroll_school ON staff_payroll(school_id, year, month);
CREATE INDEX ix_staff_payroll_status ON staff_payroll(school_id, status);
```

---

## 3. Pydantic Schemas

```python
class SalaryComponentCreate(BaseModel):
    name: str
    componentType: str  # allowance / deduction
    isPercentage: bool = False
    value: int = 0      # paise or pct*100

class GeneratePayrollRequest(BaseModel):
    month: int = Field(..., ge=1, le=12)
    year: int
    staffIds: list[UUID] | None = None   # None = all active staff
    workingDays: int = 26

class PayrollAdjustment(BaseModel):
    payrollId: UUID
    allowances: dict[str, int] = {}   # {component_name: amount_paise}
    deductions: dict[str, int] = {}
    remarks: str | None = None

class FinalizePayrollRequest(BaseModel):
    month: int
    year: int
    paymentDate: date
    paymentMode: str

class StaffPayrollResponse(BaseModel):
    id: UUID
    staffName: str
    employeeId: str
    designationName: str | None
    month: int
    year: int
    workingDays: int
    presentDays: int
    lwpDays: int
    basicSalaryPaise: int
    allowances: dict
    deductions: dict
    grossSalaryPaise: int
    totalDeductionsPaise: int
    netSalaryPaise: int
    status: str
    model_config = {"from_attributes": True}
```

---

## 4. Service (`backend/app/services/payroll_service.py`)

```python
async def generate_monthly_payroll(db, school_id, data: GeneratePayrollRequest, current_user) -> int:
    """
    For each staff member (all or specified):
      1. Get staff.monthly_salary_paise as basic.
      2. Fetch attendance for the month: present_days, lwp_days.
      3. per_day = basic / working_days
         lwp_deduction = per_day * lwp_days
      4. Apply active SalaryComponents:
         - allowances: fixed amount or % of basic
         - deductions: pf=12% if pf_number exists, esi=0.75% if esi_number exists, etc.
      5. gross = basic + sum(allowances)
      6. total_deductions = lwp_deduction + sum(deductions)
      7. net = gross - total_deductions
      8. Upsert StaffPayroll (skip if already finalized).
    Return count of records generated.
    """

async def adjust_payroll(db, school_id, data: PayrollAdjustment, current_user) -> StaffPayroll:
    """Override individual staff allowances/deductions. Recalculate net. Only on DRAFT."""

async def finalize_payroll(db, school_id, data: FinalizePayrollRequest, current_user) -> int:
    """
    Set all DRAFT payrolls for month/year to FINALIZED.
    Create ExpenseRecord in accounting for each payroll.
    Return count finalized.
    """

async def mark_paid(db, payroll_id, school_id, current_user) -> StaffPayroll:
    """Set status=paid, payment_date, payment_mode."""

async def generate_payslip_pdf(db, payroll_id, school_id) -> bytes:
    """WeasyPrint payslip with school logo, employee details, salary breakdown."""

async def get_payroll_summary(db, school_id, month, year) -> dict:
    """Total gross, net, counts by status."""
```

---

## 5. API Endpoints

```
# Salary Components
GET    /salary-components                    → list components                 [payroll:view]
POST   /salary-components                    → create component               [payroll:create]
PUT    /salary-components/{id}               → update                         [payroll:update]

# Payroll
GET    /payroll?month=&year=&status=         → list payroll records           [payroll:view]
POST   /payroll/generate                     → generate monthly payroll       [payroll:create]
PUT    /payroll/{id}/adjust                  → adjust components              [payroll:update]
POST   /payroll/finalize                     → finalize month's payroll       [payroll:update]
POST   /payroll/{id}/mark-paid              → mark individual as paid        [payroll:update]
GET    /payroll/{id}/payslip                 → download payslip PDF           [payroll:export]
GET    /payroll/summary?month=&year=         → payroll summary                [payroll:view]
GET    /payroll/staff/{staff_id}             → staff payroll history          [payroll:view]
```

---

## 6. Frontend: Payroll Pages

### Payroll Page (`/payroll`)
- **Month/Year selector**
- **Generate Payroll button**: shows confirmation with count of staff
- **Payroll table**: Employee | Dept | Basic | Gross | Deductions | Net | Status | Actions
- **Actions**: View Payslip, Adjust, Finalize
- **Bulk Finalize button**: Finalize all DRAFT for month
- **Summary bar**: Total net payable, total staff, count by status

### Payslip View Modal
- School letterhead
- Employee details
- Earnings table (basic + allowances)
- Deductions table (LWP + deductions)
- Net pay highlighted
- Download PDF button

### Salary Components Page (`/payroll/components`)
- Table of allowances and deductions
- Toggle active/inactive
- Edit %/fixed value

---

## Verification Checklist

- [ ] UNIQUE constraint on (staff_id, month, year)
- [ ] LWP days fetched from staff_leaves (status=approved, is_paid=False leave type)
- [ ] Attendance present_days fetched from staff_attendance for month
- [ ] PF deduction auto-added if staff.pf_number is set (12% of basic)
- [ ] ESI deduction auto-added if staff.esi_number is set (0.75% of gross)
- [ ] Finalized payrolls cannot be regenerated
- [ ] `finalize_payroll` creates ExpenseRecord entries
- [ ] Payslip PDF renders correctly with all components
- [ ] `adjust_payroll` recalculates gross/total_deductions/net
- [ ] Sum of allowances + basic = gross_salary_paise
