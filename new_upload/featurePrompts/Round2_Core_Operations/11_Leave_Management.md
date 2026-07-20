# Feature Prompt 11 — Leave Management

## Round: 2 of 4 — Core Operations
## Prerequisites: Prompts 01–10 complete

---

## Objective

Implement a staff leave management system covering leave type configuration, annual allocations, multi-level approval workflow (Staff → HOD → Principal), balance tracking, leave calendar, and integration with attendance.

---

## 1. Database Models (`backend/app/models/leave.py`)

```python
import uuid
from datetime import date
from sqlalchemy import String, Boolean, Date, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
import enum

class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class LeaveType(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "leave_types"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    days_per_year: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    carry_forward: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_carry_forward_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_leave_type_code"),
    )

class LeaveAllocation(Base, TimestampMixin):
    __tablename__ = "leave_allocations"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    leave_type_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("leave_types.id"), nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False)
    total_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # updated on approval
    carried_forward_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("staff_id", "leave_type_id", "academic_year_id",
                         name="uq_leave_allocation"),
    )

class StaffLeave(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "staff_leaves"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    leave_type_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("leave_types.id"), nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False)
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_count: Mapped[int] = mapped_column(Integer, nullable=False)  # NOTE: days_count (NOT total_days)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[LeaveStatus] = mapped_column(String(20), default=LeaveStatus.PENDING)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)  # NOTE: reviewed_by (NOT approved_by)
    reviewed_at: Mapped[str | None] = mapped_column(nullable=True)  # TIMESTAMPTZ NOTE: reviewed_at (NOT approved_at)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
```

---

## 2. Alembic Migration

```sql
CREATE TABLE leave_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) NOT NULL,
    description TEXT,
    days_per_year INTEGER DEFAULT 0 NOT NULL,
    is_paid BOOLEAN DEFAULT TRUE NOT NULL,
    carry_forward BOOLEAN DEFAULT FALSE NOT NULL,
    max_carry_forward_days INTEGER DEFAULT 0 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_leave_type_code UNIQUE (school_id, code)
);

CREATE TABLE leave_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    leave_type_id UUID NOT NULL REFERENCES leave_types(id),
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    total_days INTEGER DEFAULT 0 NOT NULL,
    used_days INTEGER DEFAULT 0 NOT NULL,
    carried_forward_days INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_leave_allocation UNIQUE (staff_id, leave_type_id, academic_year_id)
);

CREATE TABLE staff_leaves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    leave_type_id UUID NOT NULL REFERENCES leave_types(id),
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    days_count INTEGER NOT NULL,          -- days_count (NOT total_days)
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    reviewed_by UUID,                     -- reviewed_by (NOT approved_by)
    reviewed_at TIMESTAMPTZ,              -- reviewed_at (NOT approved_at)
    rejection_reason TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_staff_leaves_school_id ON staff_leaves(school_id);
CREATE INDEX ix_staff_leaves_staff_id ON staff_leaves(staff_id);
CREATE INDEX ix_staff_leaves_status ON staff_leaves(status);
CREATE INDEX ix_leave_allocations_school ON leave_allocations(school_id, academic_year_id);
```

---

## 3. Seed Data — Default Leave Types

```python
DEFAULT_LEAVE_TYPES = [
    {"name": "Casual Leave",     "code": "CL",  "days_per_year": 12, "is_paid": True,  "carry_forward": False},
    {"name": "Sick Leave",       "code": "SL",  "days_per_year": 10, "is_paid": True,  "carry_forward": False},
    {"name": "Earned Leave",     "code": "EL",  "days_per_year": 15, "is_paid": True,  "carry_forward": True, "max_carry_forward_days": 15},
    {"name": "Maternity Leave",  "code": "ML",  "days_per_year": 90, "is_paid": True,  "carry_forward": False},
    {"name": "Paternity Leave",  "code": "PL",  "days_per_year": 5,  "is_paid": True,  "carry_forward": False},
    {"name": "Leave Without Pay","code": "LWP", "days_per_year": 0,  "is_paid": False, "carry_forward": False},
]
# Seeded via endpoint: POST /leave-types/seed (admin only)
```

---

## 4. Pydantic Schemas

```python
class LeaveTypeCreate(BaseModel):
    name: str
    code: str = Field(..., max_length=10)
    daysPerYear: int = 0
    isPaid: bool = True
    carryForward: bool = False
    maxCarryForwardDays: int = 0

class LeaveAllocationBulk(BaseModel):
    academicYearId: UUID
    leaveTypeId: UUID
    totalDays: int
    staffIds: list[UUID] | None = None  # None = all active staff

class StaffLeaveApply(BaseModel):
    leaveTypeId: UUID
    fromDate: date
    toDate: date
    reason: str | None = None

class StaffLeaveReview(BaseModel):
    action: Literal["approve", "reject"]
    rejectionReason: str | None = None

class LeaveBalanceResponse(BaseModel):
    leaveTypeId: UUID
    leaveTypeName: str
    totalDays: int
    usedDays: int
    remainingDays: int
    carriedForwardDays: int

class StaffLeaveResponse(BaseModel):
    id: UUID
    staffName: str
    leaveTypeName: str
    fromDate: date
    toDate: date
    daysCount: int            # days_count field
    reason: str | None
    status: str
    reviewedBy: UUID | None
    reviewedAt: str | None
    model_config = {"from_attributes": True}
```

---

## 5. Service (`backend/app/services/leave_service.py`)

```python
async def apply_leave(db, school_id, staff_id, data: StaffLeaveApply, current_user) -> StaffLeave:
    """
    1. Validate from_date <= to_date.
    2. Calculate days_count (skip Sundays + holidays).
    3. Check leave balance (allocation.total_days + carried_forward - used_days >= days_count).
    4. Check no overlapping pending/approved leave for same staff.
    5. Create StaffLeave record.
    6. Notify HOD/reporting manager (Celery task).
    """

async def review_leave(db, leave_id, school_id, data: StaffLeaveReview, current_user) -> StaffLeave:
    """
    Permission: principal or hod for their department.
    On approve: allocation.used_days += leave.days_count
    On reject: set rejection_reason.
    Set reviewed_by = current_user.id, reviewed_at = utcnow()
    Notify staff.
    """

async def cancel_leave(db, leave_id, school_id, current_user) -> StaffLeave:
    """
    Staff can cancel own pending leave.
    Principal can cancel any.
    On cancel (if was approved): allocation.used_days -= days_count
    """

async def allocate_leaves(db, school_id, data: LeaveAllocationBulk, current_user) -> int:
    """
    Bulk create/update leave_allocations for all (or specified) staff.
    Return count of records created/updated.
    """

async def carry_forward_leaves(db, school_id, from_year_id, to_year_id, current_user) -> int:
    """
    For each leave_type with carry_forward=True:
      remaining = allocation.total_days - allocation.used_days
      carried = min(remaining, leave_type.max_carry_forward_days)
      Create new allocation in to_year with carried_forward_days = carried
    """

async def get_leave_balance(db, staff_id, school_id, academic_year_id) -> list:
    """Return list of LeaveBalanceResponse for all active leave types."""

async def calculate_days_count(from_date: date, to_date: date, school_id, db) -> int:
    """Count working days between dates: skip Sundays + holidays from holidays table."""
```

---

## 6. API Endpoints

```
# Leave Types  
GET    /leave-types                          → list leave types                [leave:view]
POST   /leave-types                          → create leave type               [leave:create]
PUT    /leave-types/{id}                     → update leave type               [leave:update]
POST   /leave-types/seed                     → seed defaults                   [leave:create]

# Leave Allocations
GET    /leave-allocations?year_id=           → list allocations for year       [leave:view]
POST   /leave-allocations/bulk               → bulk allocate to staff          [leave:create]
POST   /leave-allocations/carry-forward      → carry forward to new year       [leave:create]

# Leave Requests
GET    /leaves?status=&staff_id=             → list leave requests             [leave:view]
POST   /leaves                               → apply for leave                 [leave:create]
GET    /leaves/{id}                          → leave detail                    [leave:view]
POST   /leaves/{id}/review                   → approve/reject                  [leave:update]
POST   /leaves/{id}/cancel                   → cancel leave                    [leave:update]

# Self-service (staff viewing own leave)
GET    /leaves/my                            → own leave requests              [auth]
GET    /leaves/my/balance                    → own leave balance               [auth]
GET    /leaves/my/calendar                   → calendar view own leaves        [auth]
```

---

## 7. Frontend: Leave Pages

### Leave Management Page (`/leaves`) — Admin
- **Tabs**: Pending | All Requests | Calendar | Allocations | Leave Types
- **Pending tab**: Card view of pending leaves with Approve/Reject buttons
- **All Requests tab**: Table with filters (staff, type, status, date range)
- **Calendar tab**: Monthly calendar with leave events color-coded by type
- **Allocations tab**: Department-wise balance table
- **Leave Types tab**: CRUD for leave types

### My Leave Page (`/my-leave`) — Staff
- **Leave Balance cards**: one per leave type with used/remaining progress bar
- **Apply Leave form**: date-picker with real-time working days calculation
- **Request History table**: past requests with status badges
- **Calendar**: own leave calendar

---

## 8. Custom Hooks

```typescript
// hooks/useLeave.ts
export function useLeaveBalance(staffId: string, yearId: string) { ... }
export function useLeaveRequests(filters: LeaveFilters) { ... }
export function useApplyLeave() { ... }
export function useReviewLeave() { ... }
export function useLeaveCalendar(month: number, year: number) { ... }
```

---

## Verification Checklist

- [ ] Leave application calculates `days_count` (skips Sundays + holidays)
- [ ] Balance check prevents applying if insufficient balance
- [ ] Overlap check prevents duplicate leave dates
- [ ] `days_count` field name used (NOT `total_days`)
- [ ] `reviewed_by` / `reviewed_at` field names used (NOT `approved_by` / `approved_at`)
- [ ] Approval increments `used_days` in allocation
- [ ] Cancellation of approved leave decrements `used_days`
- [ ] Carry-forward endpoint creates new year allocations correctly
- [ ] Bulk allocation endpoint creates records for all staff
- [ ] Self-service my-leave returns only current_user's staff leaves
