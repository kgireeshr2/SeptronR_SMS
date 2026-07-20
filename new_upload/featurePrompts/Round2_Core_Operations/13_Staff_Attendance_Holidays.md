# Feature Prompt 13 — Staff Attendance & Holiday Management

## Round: 2 of 4 — Core Operations
## Prerequisites: Prompts 01–11 complete

---

## Objective

Implement staff attendance tracking (manual, QR code, biometric import), absence alerts, and school holiday management including auto-integration with leave and student attendance modules.

---

## 1. Database Models (`backend/app/models/staff_attendance.py`)

```python
import uuid
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMPTZ
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
import enum

class CheckinMethod(str, enum.Enum):
    MANUAL = "manual"
    BIOMETRIC = "biometric"
    QR = "qr"
    AUTO = "auto"

class StaffAttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    ON_LEAVE = "on_leave"
    HOLIDAY = "holiday"

class StaffAttendance(Base, TimestampMixin):
    __tablename__ = "staff_attendance"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    attendance_date: Mapped["date"] = mapped_column(Date, nullable=False)
    check_in_time: Mapped[str | None] = mapped_column(TIMESTAMPTZ, nullable=True)  # NOTE: check_in_time as TIMESTAMPTZ (NOT TIME)
    check_out_time: Mapped[str | None] = mapped_column(TIMESTAMPTZ, nullable=True) # NOTE: check_out_time as TIMESTAMPTZ (NOT TIME)
    status: Mapped[StaffAttendanceStatus] = mapped_column(String(20), default=StaffAttendanceStatus.ABSENT)
    method: Mapped[CheckinMethod] = mapped_column(String(20), default=CheckinMethod.MANUAL)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    marked_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("staff_id", "attendance_date", name="uq_staff_attendance_date"),
    )
```

---

## 2. Holiday Model (`backend/app/models/holiday.py`)

```python
class HolidayType(str, enum.Enum):
    NATIONAL = "national"
    REGIONAL = "regional"
    SCHOOL = "school"
    EXAM = "exam"

class Holiday(Base, TimestampMixin):
    __tablename__ = "holidays"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped["date"] = mapped_column(Date, nullable=False)
    end_date: Mapped["date"] = mapped_column(Date, nullable=False)
    type: Mapped[HolidayType] = mapped_column(String(20), nullable=False)  # NOTE: type (NOT holiday_type)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

---

## 3. Alembic Migration

```sql
CREATE TABLE staff_attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    check_in_time TIMESTAMPTZ,   -- check_in_time (TIMESTAMPTZ, NOT TIME)
    check_out_time TIMESTAMPTZ,  -- check_out_time (TIMESTAMPTZ, NOT TIME)
    status VARCHAR(20) DEFAULT 'absent' NOT NULL,
    method VARCHAR(20) DEFAULT 'manual' NOT NULL,
    remarks TEXT,
    marked_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_staff_attendance_date UNIQUE (staff_id, attendance_date)
);

CREATE INDEX ix_staff_attendance_school ON staff_attendance(school_id);
CREATE INDEX ix_staff_attendance_date ON staff_attendance(school_id, attendance_date);

CREATE TABLE holidays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    name VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    type VARCHAR(20) NOT NULL,   -- type (NOT holiday_type)
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_holidays_school_year ON holidays(school_id, academic_year_id);
```

---

## 4. Pydantic Schemas

```python
class StaffAttendanceMark(BaseModel):
    staffId: UUID
    attendanceDate: date
    status: str = "present"
    checkInTime: datetime | None = None   # full TIMESTAMPTZ
    checkOutTime: datetime | None = None  # full TIMESTAMPTZ
    method: str = "manual"
    remarks: str | None = None

class StaffAttendanceBulk(BaseModel):
    attendanceDate: date
    records: list[StaffAttendanceMark]

class BiometricImportRow(BaseModel):
    employeeId: str
    punchTime: datetime  # TIMESTAMPTZ in CSV as ISO string

class HolidayCreate(BaseModel):
    name: str
    startDate: date
    endDate: date
    type: str  # national/regional/school/exam
    academicYearId: UUID
    description: str | None = None

class StaffAttendanceResponse(BaseModel):
    id: UUID
    staffName: str
    employeeId: str
    attendanceDate: date
    checkInTime: datetime | None
    checkOutTime: datetime | None
    status: str
    method: str
    model_config = {"from_attributes": True}

class HolidayResponse(BaseModel):
    id: UUID
    name: str
    startDate: date
    endDate: date
    type: str
    daysCount: int
    model_config = {"from_attributes": True}
```

---

## 5. Service (`backend/app/services/staff_attendance_service.py`)

```python
async def mark_staff_attendance(db, school_id, data: StaffAttendanceMark, current_user):
    """
    Upsert staff attendance for the date.
    If status=present and is_holiday(date): override status=holiday.
    Audit log.
    """

async def bulk_mark_attendance(db, school_id, data: StaffAttendanceBulk, current_user) -> int:
    """Mark attendance for all staff in one request. Returns count."""

async def import_biometric_csv(db, redis, school_id, file: UploadFile, current_user) -> dict:
    """
    CSV format: employee_id, punch_datetime (ISO), punch_type (I/O)
    Algorithm:
      - For each employee, find first IN as check_in_time, last OUT as check_out_time.
      - Calculate duration; if < 4h → half_day, if < grace_minutes late → late.
      - Upsert StaffAttendance.
    Return: {total_rows, processed, skipped_unknown, errors[]}
    """

async def get_daily_attendance(db, school_id, date, dept_id=None):
    """Return all staff attendance for a date, optionally filtered by department."""

async def get_monthly_summary(db, school_id, staff_id, month, year) -> dict:
    """Return monthly stats: present/absent/late/leave counts, calendar data."""

async def get_absent_staff_today(db, school_id) -> list:
    """Staff who are absent today and have not applied leave."""

async def is_holiday(db, school_id, check_date: date) -> Holiday | None:
    """Check if date falls within any active holiday range."""
```

### Holiday Service (`backend/app/services/holiday_service.py`)

```python
async def create_holiday(db, school_id, data: HolidayCreate, current_user) -> Holiday:
    """
    Create holiday.
    Trigger: auto-mark all staff_attendance for holiday dates as holiday.
    Trigger: auto-mark all attendance_sessions for holiday dates as is_holiday=True.
    """

async def delete_holiday(db, holiday_id, school_id, current_user):
    """Soft delete. Reverse auto-marking of staff_attendance."""

async def get_holidays_by_year(db, school_id, academic_year_id) -> list[Holiday]:
    """All holidays for the year, ordered by start_date."""

async def get_upcoming_holidays(db, school_id, days_ahead=30) -> list[Holiday]:
    """Holidays in next N days."""
```

---

## 6. Celery Tasks

File: `backend/app/tasks/staff_attendance_tasks.py`

```python
@celery_app.task(name="check_absent_staff_notifications", queue="notifications")
def check_absent_staff_notifications():
    """
    Celery Beat: runs every 15 minutes starting at 9:00 AM.
    For each school where current time > grace_period_end:
      1. Get all active staff with no check-in today.
      2. If is_holiday(today): skip.
      3. Mark as absent if not already marked.
      4. Send SMS/WhatsApp to absent staff: "Dear {name}, you are marked absent..."
      5. Notify principal/admin.
    """

@celery_app.task(name="auto_mark_holiday_attendance", queue="scheduled")
def auto_mark_holiday_attendance(holiday_id: str, school_id: str):
    """
    When a holiday is created:
      - For each date in holiday range:
        - Mark all staff_attendance as holiday if not already marked.
        - Update attendance_sessions is_holiday=True.
    """
```

Celery Beat schedule (add to `celery_app.py`):
```python
beat_schedule = {
    "check-absent-staff-every-15min": {
        "task": "check_absent_staff_notifications",
        "schedule": crontab(minute="*/15", hour="9-12"),
    }
}
```

---

## 7. QR Code Check-In Flow

```python
# Endpoint: POST /staff/qr-checkin
# Body: { qr_token: str }
# QR tokens are per-staff, valid for 30 seconds (signed JWT with staff_id + exp)
# Security: rate limit 1 check-in per staff per 5 minutes

async def qr_checkin(db, school_id, qr_token: str):
    """
    1. Decode & verify JWT qr_token (staff_id, school_id, exp).
    2. Mark check_in_time = utcnow(), method = qr.
    3. If already checked in today: mark check_out_time.
    """

async def generate_staff_qr_token(staff_id: UUID, school_id: UUID) -> str:
    """Create 30-second JWT for QR code display on staff screen."""
```

---

## 8. API Endpoints

```
# Staff Attendance
GET    /staff-attendance?date=&dept_id=       → daily attendance               [attendance:view]
POST   /staff-attendance/mark                 → single mark                    [attendance:create]
POST   /staff-attendance/bulk                 → bulk mark                      [attendance:create]
POST   /staff-attendance/import-biometric     → upload biometric CSV           [attendance:create]
GET    /staff-attendance/monthly/{staff_id}   → monthly summary               [attendance:view]
GET    /staff-attendance/absent-today         → absent staff today             [attendance:view]
POST   /staff/qr-checkin                      → QR check-in                   [auth]
GET    /staff/qr-token                        → get own QR token              [auth]

# Holidays
GET    /holidays?academic_year_id=            → list holidays                  [attendance:view]
POST   /holidays                              → create holiday                 [attendance:create]
PUT    /holidays/{id}                         → update holiday                 [attendance:update]
DELETE /holidays/{id}                         → delete holiday                 [attendance:delete]
GET    /holidays/upcoming                     → next 30 days                   [attendance:view]
```

---

## 9. Frontend: Pages

### Staff Attendance Page (`/staff-attendance`)
- **Daily View**: Date picker → Table with all staff (Department column, status colored badges, check-in/out times)
- **Bulk Mark**: Select staff, set status (bulk for department)
- **Import Biometric**: Upload CSV button, preview parsed data, confirm import

### Holiday Management Page (`/holidays`)
- Calendar view (FullCalendar month view, holidays highlighted)
- Holiday list with date ranges and types
- Add Holiday modal with date range picker + type selector
- Auto-shows impact: "X staff attendance records will be updated"

### Staff Attendance Self-Service (within `/my-profile`)
- **My Attendance tab**: Monthly calendar, today's check-in/out time, QR code for check-in

---

## Verification Checklist

- [ ] `check_in_time` and `check_out_time` are `TIMESTAMPTZ` (not `TIME`)
- [ ] `Holiday.type` field name used (NOT `holiday_type`)
- [ ] Unique constraint `uq_staff_attendance_date` on (staff_id, attendance_date)
- [ ] Holiday creation auto-marks staff_attendance as "holiday" for date range
- [ ] Holiday creation marks attendance_sessions.is_holiday=True
- [ ] Biometric CSV import handles first-IN/last-OUT per employee correctly
- [ ] QR check-in JWT tokens expire after 30 seconds
- [ ] Celery Beat task runs every 15min (9 AM–12 PM window)
- [ ] Absent notification skips if is_holiday(today) = True
- [ ] `get_monthly_summary` includes on_leave days from staff_leaves table
