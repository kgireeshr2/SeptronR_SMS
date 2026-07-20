# Feature Prompt 12 — Student Attendance

## Round: 2 of 4 — Core Operations
## Prerequisites: Prompts 01–09 complete

---

## Objective

Implement class-wise student attendance marking (present/absent/late/half-day/holiday), bulk marking, absent parent notifications via Celery, monthly attendance reports, and low-attendance tracking.

---

## 1. Database Models (`backend/app/models/attendance.py`)

```python
import uuid
from datetime import date
from sqlalchemy import String, Boolean, Date, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
import enum

class AttendanceStatus(str, enum.Enum):
    PRESENT = "P"
    ABSENT = "A"
    LATE = "L"
    HALF_DAY = "H"
    HOLIDAY = "HOL"
    LEAVE = "LEV"

class SessionType(str, enum.Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    FULL_DAY = "full_day"

class AttendanceSession(Base, TimestampMixin):
    """One session per section per date."""
    __tablename__ = "attendance_sessions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("sections.id"), nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    session_type: Mapped[SessionType] = mapped_column(String(20), default=SessionType.FULL_DAY)
    marked_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)
    is_holiday: Mapped[bool] = mapped_column(Boolean, default=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("section_id", "attendance_date", "session_type",
                         name="uq_attendance_session"),
    )

    records: Mapped[list["StudentAttendance"]] = relationship(
        "StudentAttendance", back_populates="session")


class StudentAttendance(Base, TimestampMixin):
    """Individual student attendance record."""
    __tablename__ = "student_attendance"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(String(5), default=AttendanceStatus.PRESENT)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    session: Mapped[AttendanceSession] = relationship(
        "AttendanceSession", back_populates="records")

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_student_attendance"),
    )
```

---

## 2. Alembic Migration

```sql
CREATE TABLE attendance_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES sections(id),
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    attendance_date DATE NOT NULL,
    session_type VARCHAR(20) DEFAULT 'full_day' NOT NULL,
    marked_by UUID NOT NULL REFERENCES users(id),
    is_holiday BOOLEAN DEFAULT FALSE NOT NULL,
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_attendance_session UNIQUE (section_id, attendance_date, session_type)
);

CREATE INDEX ix_attendance_sessions_school ON attendance_sessions(school_id);
CREATE INDEX ix_attendance_sessions_date ON attendance_sessions(school_id, attendance_date);

CREATE TABLE student_attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES attendance_sessions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    status VARCHAR(5) DEFAULT 'P' NOT NULL,  -- P/A/L/H/HOL/LEV
    remarks TEXT,
    notification_sent BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_student_attendance UNIQUE (session_id, student_id)
);

CREATE INDEX ix_student_attendance_student ON student_attendance(student_id);
CREATE INDEX ix_student_attendance_session ON student_attendance(session_id);
```

---

## 3. Pydantic Schemas

```python
class AttendanceMarkRequest(BaseModel):
    sectionId: UUID
    attendanceDate: date
    sessionType: str = "full_day"
    records: list[StudentAttendanceRecord]
    remarks: str | None = None

class StudentAttendanceRecord(BaseModel):
    studentId: UUID
    status: str  # P/A/L/H
    remarks: str | None = None

class AttendanceSessionResponse(BaseModel):
    id: UUID
    sectionId: UUID
    attendanceDate: date
    sessionType: str
    totalStudents: int
    presentCount: int
    absentCount: int
    lateCount: int
    markedBy: str
    model_config = {"from_attributes": True}

class StudentMonthlyAttendance(BaseModel):
    studentId: UUID
    admissionNumber: str
    studentName: str
    presentDays: int
    absentDays: int
    lateDays: int
    totalWorkingDays: int
    attendancePercent: float
    dailyStatus: dict[str, str]  # date string → status

class SectionAttendanceResponse(BaseModel):
    sectionId: UUID
    sectionName: str
    date: date
    students: list[dict]  # [{studentId, name, rollNumber, status}]
    alreadyMarked: bool
```

---

## 4. Service (`backend/app/services/attendance_service.py`)

```python
async def mark_attendance(db, redis, school_id, data: AttendanceMarkRequest, current_user):
    """
    1. Check if session already exists for (section_id, date, session_type).
       If already marked and locked(>2 hours old): return 409 with existing session data.
    2. Check if attendance_date is a holiday (from holidays table).
    3. Create or update AttendanceSession.
    4. Upsert StudentAttendance records.
    5. Enqueue absent notification task with delay = absent_notify_delay_minutes setting.
    6. Audit log.
    """

async def get_section_for_marking(db, school_id, section_id, date):
    """Return section with all current enrolled students + existing attendance if any."""

async def get_monthly_report(db, school_id, section_id, month, year):
    """
    Return StudentMonthlyAttendance list.
    Cal total working days = school days in month (exclude Sundays + holidays).
    """

async def get_student_attendance_summary(db, student_id, school_id, academic_year_id):
    """
    Return cumulative stats for a student.
    Total days, present_days, absent_days, attendance_pct.
    """

async def get_low_attendance_students(db, school_id, threshold_pct: float = 75.0):
    """Return students below threshold_pct for current academic year."""

async def get_pending_sections(db, school_id, date):
    """Return sections that have NOT marked attendance for given date."""

async def generate_monthly_pdf(db, school_id, section_id, month, year) -> bytes:
    """Render monthly attendance sheet PDF via WeasyPrint."""
```

---

## 5. Celery Task — Absent Notifications

File: `backend/app/tasks/attendance_tasks.py`

```python
@celery_app.task(name="send_absent_notifications", queue="notifications")
def send_absent_notifications(session_id: str, school_id: str):
    """
    1. Load all StudentAttendance for session where status='A' and notification_sent=False.
    2. For each absent student:
       a. Load student parents (StudentParent with is_primary=True).
       b. Compose SMS: "Dear {parent_name}, {student_name} was absent on {date}."
       c. Send SMS via configured provider (MSG91/Twilio based on school settings).
       d. Mark notification_sent=True.
    3. Wrapped in try/except; failures logged but don't retry individual sends.
    """

# Scheduled with delay from settings
# apply_async(kwargs=..., countdown=absent_notify_delay_minutes*60)
```

---

## 6. API Endpoints

```
GET    /attendance/section/{section_id}/date/{date}  → get section attendance  [attendance:view]
POST   /attendance/mark                              → mark/update attendance  [attendance:create]
GET    /attendance/monthly?section_id=&month=&year= → monthly attendance data [attendance:view]
GET    /attendance/monthly/pdf?section_id=&month=   → monthly PDF download    [attendance:export]
GET    /attendance/summary/student/{student_id}      → student yearly summary  [attendance:view]
GET    /attendance/low?threshold=75                  → low attendance students [attendance:view]
GET    /attendance/pending/today                     → pending sections today  [attendance:view]
GET    /attendance/calendar?section_id=&month=      → month calendar view     [attendance:view]
POST   /attendance/holiday/{date}                   → mark date as holiday    [attendance:update]
```

---

## 7. Frontend: Attendance Pages

### Mark Attendance Page (`/attendance/mark`)
- **Section selector**: Class → Section dropdown (teacher sees only their sections)
- **Date picker**: defaults to today
- **Attendance table**:
  - Columns: Roll No | Photo | Name | P | A | L | H (radio toggle)
  - "Mark All Present" button at top
  - Individual toggles
  - Remarks per student input
- **Submit**: disabled if date is holiday; shows warning if re-marking within 2 hours
- **Success**: shows summary card (Present: X, Absent: Y, Late: Z)

### Attendance Reports Page (`/attendance/reports`)
- **Tab 1: Monthly Sheet**
  - Section + Month/Year filters
  - Grid: Rows = students, Columns = dates (1–31)
  - Color-coded cells: P=green, A=red, L=yellow, H=orange, HOL=grey
  - Summary row at bottom
  - PDF download button
- **Tab 2: Student Summary**
  - Search student, show yearly summary + chart
- **Tab 3: Low Attendance**
  - Table of students below threshold with parent contact

### Attendance Dashboard Widget
- Today's status: sections marked vs total
- Quick link to mark for teacher's section

---

## 8. Custom Hooks

```typescript
// hooks/useAttendance.ts
export function useSectionForMarking(sectionId: string, date: string) { ... }
export function useMarkAttendance() { ... }
export function useMonthlyAttendance(sectionId, month, year) { ... }
export function useStudentAttendanceSummary(studentId, yearId) { ... }
export function useLowAttendanceStudents(threshold?: number) { ... }
export function usePendingSections(date: string) { ... }
```

---

## Verification Checklist

- [ ] Duplicate session for same (section, date, session_type) returns 409 with existing data
- [ ] Holiday dates cannot be marked (returns 400 with reason)
- [ ] `notification_sent` flag correctly set after absent SMS sent
- [ ] Monthly report calculates working days excluding Sundays + holidays
- [ ] Low-attendance endpoint returns students below threshold correctly
- [ ] Monthly PDF renders grid with all 31 days
- [ ] Teacher can only see/mark attendance for their assigned sections
- [ ] "Mark All Present" sets all to P, individual toggles override
- [ ] Absent notification Celery task dispatched with correct delay from settings
- [ ] Re-marking attendance (update) works within allowed window
