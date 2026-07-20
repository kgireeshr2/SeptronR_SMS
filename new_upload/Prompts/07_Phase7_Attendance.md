# PHASE 7 — ATTENDANCE MANAGEMENT

## Pre-Requisite
Phases 1–6 complete. Students enrolled in sections, staff created, timetable defined.

## Objective
Full attendance system: student daily attendance (with sessions), staff attendance, biometric import, reports, notifications to parents on absence.

---

## 7.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 10: Attendance — TWO-TABLE DESIGN (not a single attendance table)

-- Table 1: one row per section+date+session (session header)
attendance_sessions (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    section_id UUID FK→sections ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    date DATE NOT NULL,
    session_type VARCHAR(20) DEFAULT 'full_day',  -- full_day|morning|afternoon|period
    taken_by UUID FK→users,    -- teacher who took attendance
    is_finalized BOOL DEFAULT FALSE,
    finalized_at TIMESTAMPTZ,
    created_at, updated_at,
    UNIQUE(section_id, date, session_type)
)

-- Table 2: one row per student per session (actual attendance status)
student_attendance (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    session_id UUID FK→attendance_sessions ON DELETE CASCADE,
    student_id UUID FK→students ON DELETE CASCADE,
    status attendance_status DEFAULT 'present',
        -- ENUM: present|absent|late|half_day|holiday|leave
    remarks TEXT,
    created_at, updated_at,
    UNIQUE(session_id, student_id)
)
-- NOTE: student_attendance does NOT have date, section_id, academic_year_id directly.
-- These are accessed via JOIN attendance_sessions. Query pattern:
--   SELECT sa.* FROM student_attendance sa
--   JOIN attendance_sessions asn ON sa.session_id = asn.id
--   WHERE asn.section_id = :sid AND asn.date = :date

staff_attendance (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    staff_id UUID FK→staff ON DELETE CASCADE,
    date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'present',     -- present|absent|half_day|on_leave
    check_in TIMESTAMPTZ,    -- ⚠️ TIMESTAMPTZ, not TIME (field name: check_in not in_time)
    check_out TIMESTAMPTZ,   -- ⚠️ TIMESTAMPTZ, not TIME (field name: check_out not out_time)
    source VARCHAR(20) DEFAULT 'manual',      -- manual|biometric
    remarks TEXT,
    marked_by UUID FK→users,
    created_at, updated_at,
    UNIQUE(staff_id, date)
)

attendance_settings (
    school_id UUID PK FK→schools,
    working_days JSONB DEFAULT '[1,2,3,4,5]',   -- 1=Mon...7=Sun
    sessions_enabled VARCHAR(20) DEFAULT 'full_day',
    low_attendance_threshold_pct SMALLINT DEFAULT 75,
    absent_notify_delay_minutes SMALLINT DEFAULT 30,
    notify_parents_sms BOOL DEFAULT TRUE,
    notify_parents_whatsapp BOOL DEFAULT TRUE
)

holidays (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    name VARCHAR(200) NOT NULL, date DATE NOT NULL,
    holiday_type VARCHAR(50),   -- national|regional|school|exam
    description TEXT, is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, date)
)
```

> **Critical architecture note**: Marking attendance requires **two steps**:
> 1. `INSERT INTO attendance_sessions ... ON CONFLICT DO NOTHING` → get `session_id`
> 2. `INSERT INTO student_attendance (session_id, student_id, status) ... ON CONFLICT (session_id, student_id) DO UPDATE SET status = EXCLUDED.status`
> 
> To query a student's attendance history, always JOIN `student_attendance → attendance_sessions`.


---

## 7.2 SQLAlchemy Models (`backend/app/models/attendance.py`)

```python
class AttendanceStatus(str, PyEnum):
    present = "present"; absent = "absent"; late = "late"
    half_day = "half_day"; holiday = "holiday"; leave = "leave"

# TWO models for the two-table design:
class AttendanceSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    # table: attendance_sessions
    # section_id, date, session_type, taken_by, is_finalized
    ...

class StudentAttendance(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    # table: student_attendance
    # session_id FK→attendance_sessions, student_id, status, remarks
    ...

class StaffAttendance(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    # check_in: Mapped[Optional[datetime]] (TIMESTAMPTZ, not TIME)
    # check_out: Mapped[Optional[datetime]] (TIMESTAMPTZ, not TIME)
    ...

class Holiday(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
```

---

## 7.3 Pydantic Schemas

```python
class AttendanceMarkEntry(BaseModel):
    student_id: UUID
    status: AttendanceStatus
    remarks: Optional[str]

class AttendanceMarkRequest(BaseModel):
    section_id: UUID
    academic_year_id: UUID
    date: date
    session_type: str = "full_day"   # NOTE: field is 'session_type' not 'session'
    entries: List[AttendanceMarkEntry]
    # Service will: 1) upsert attendance_session, 2) bulk upsert student_attendance

class AttendanceUpdateRequest(BaseModel):
    status: AttendanceStatus
    remarks: Optional[str]

class AttendanceRecord(BaseModel):
    student_id: UUID
    student_name: str
    admission_number: str
    date: date
    status: str
    session: str
    remarks: Optional[str]
    marked_at: Optional[datetime]

class SectionAttendanceSummary(BaseModel):
    section_id: UUID
    date: date
    session: str
    total: int; present: int; absent: int; late: int; half_day: int; leave: int
    attendance_pct: float
    entries: List[AttendanceRecord]

class StudentAttendanceSummary(BaseModel):
    student_id: UUID
    student_name: str
    total_working_days: int
    days_present: int; days_absent: int; days_late: int; days_leave: int
    attendance_pct: float
    is_low: bool

class StaffAttendanceMarkRequest(BaseModel):
    staff_id: UUID
    date: date
    status: str   # present|absent|half_day|on_leave
    check_in: Optional[datetime]   # ⚠️ TIMESTAMPTZ datetime (not 'in_time: time')
    check_out: Optional[datetime]  # ⚠️ TIMESTAMPTZ datetime (not 'out_time: time')
    source: str = "manual"         # manual|biometric
    remarks: Optional[str]

class HolidayCreate(BaseModel):
    name: str
    date: date
    holiday_type: str = "school"
    description: Optional[str]
    academic_year_id: UUID

class AttendanceReportParams(BaseModel):
    section_id: Optional[UUID]
    class_id: Optional[UUID]
    academic_year_id: UUID
    from_date: date; to_date: date
    student_id: Optional[UUID]
    status: Optional[str]
    min_attendance_pct: Optional[float]
    max_attendance_pct: Optional[float]
```

---

## 7.4 Repository Layer

```python
class AttendanceRepository:
    # Two-table design: attendance_sessions + student_attendance
    async def get_or_create_session(self, school_id: str, section_id: str, year_id: str,
                                    date_: date, session_type: str, taken_by: str) -> AttendanceSession: ...
    async def bulk_upsert_student_attendance(self, session_id: str, schema_id: str,
                                              entries: list) -> int: ...
    async def get_session(self, section_id: str, date_: date, session_type: str) -> Optional[AttendanceSession]: ...
    async def get_student_attendance_for_session(self, session_id: str) -> List[StudentAttendance]: ...
    async def get_attendance_by_student_date(self, student_id: str, date_: date, session_type: str) -> Optional[StudentAttendance]: ...
    async def get_student_summary(self, student_id: str, year_id: str,
                                  from_date: date, to_date: date) -> StudentAttendanceSummary: ...
    async def get_class_monthly_summary(self, class_id: str, year_id: str, month: int, year: int) -> List[dict]: ...
    async def get_low_attendance_students(self, school_id: str, year_id: str, threshold_pct: float) -> List[dict]: ...
    async def count_absent_today(self, school_id: str, date_: date) -> int: ...
    async def list_absences_for_notification(self, school_id: str, date_: date,
                                             delay_minutes: int) -> List[dict]: ...
    async def get_holiday(self, school_id: str, date_: date) -> Optional[Holiday]: ...
    async def is_working_day(self, school_id: str, date_: date) -> bool: ...
    async def list_holidays(self, school_id: str, year_id: str, from_date: Optional[date], to_date: Optional[date]) -> List[Holiday]: ...

class StaffAttendanceRepository:
    async def bulk_upsert(self, school_id: str, entries: list, marked_by: str) -> int: ...
    async def get_by_staff_date(self, staff_id: str, date_: date) -> Optional[StaffAttendance]: ...
    async def get_staff_monthly(self, staff_id: str, month: int, year: int) -> List[StaffAttendance]: ...
    async def import_biometric(self, school_id: str, records: list) -> dict: ...
```

---

## 7.5 Service Layer

```python
async def mark_attendance(school_id: str, data: AttendanceMarkRequest, marked_by: str) -> SectionAttendanceSummary:
    """
    1. Check if date is a holiday → return 400 "Cannot mark on holiday"
    2. Check if date is in working_days (day-of-week) → warn but allow override
    3. Bulk upsert attendance entries
    4. Enqueue Celery: schedule_absence_notifications(school_id, date, session, delay_minutes)
    5. Return section summary
    """

@celery.task(queue="notifications", countdown=delay_seconds)
def schedule_absence_notifications(school_id: str, date: str, session: str):
    """
    1. Load all students marked absent/late for school+date+session
    2. For each student: get primary_contact parent's phone/email
    3. If notify_parents_sms: send SMS
    4. If notify_parents_whatsapp: send WhatsApp message
    5. Log notifications sent in notification_logs
    """

async def import_biometric_csv(school_id: str, file: UploadFile, date_: date, marked_by: str) -> dict:
    """
    CSV columns: employee_id, in_time, out_time
    Parse → match staff by employee_id → upsert StaffAttendance
    Returns {success: N, failed: [{employee_id, reason}]}
    """

async def get_attendance_report(school_id: str, params: AttendanceReportParams) -> List[StudentAttendanceSummary]:
    """
    Calculate: working days in range (exclude holidays + non-working days)
    Per student: count present/absent/late/leave for range
    Compute attendance_pct = (present + half_day*0.5 + late) / total_working_days
    """

async def generate_monthly_attendance_sheet_pdf(section_id: str, year_id: str, month: int, year: int) -> bytes:
    """Jinja2 grid: rows=students, cols=dates, cells=P/A/L/H etc."""
```

---

## 7.6 API Endpoints

### Student Attendance
```
GET  /api/v1/attendance/section/{section_id}  → get today's attendance for section [attendance:view]
     ?date=YYYY-MM-DD&session=full_day
POST /api/v1/attendance/section/{section_id}  → mark/update attendance [attendance:mark]
PUT  /api/v1/attendance/{id}                  → update single record [attendance:mark]
GET  /api/v1/attendance/student/{student_id}  → student monthly summary [attendance:view]
     ?from=YYYY-MM-DD&to=YYYY-MM-DD
GET  /api/v1/attendance/report                → bulk report (class/section/date-range) [attendance:report]
GET  /api/v1/attendance/low-attendance        → students below threshold [attendance:report]
GET  /api/v1/attendance/export                → Excel export [attendance:export]
GET  /api/v1/attendance/section/{section_id}/monthly-sheet → PDF attendance sheet [attendance:export]
```

### Staff Attendance
```
GET  /api/v1/staff-attendance                 → list for date [staff_attendance:view]
     ?date=YYYY-MM-DD
POST /api/v1/staff-attendance                 → mark staff attendance [staff_attendance:mark]
POST /api/v1/staff-attendance/biometric-import → CSV upload [staff_attendance:mark]
GET  /api/v1/staff-attendance/report          → monthly report [staff_attendance:report]
     ?month=N&year=N
```

### Holidays
```
GET  /api/v1/holidays                         → list [holidays:view]
POST /api/v1/holidays                         → create [holidays:manage]
PUT  /api/v1/holidays/{id}                    → update
DELETE /api/v1/holidays/{id}                  → delete
POST /api/v1/holidays/bulk                    → bulk create from JSON array
```

---

## 7.7 Frontend Pages

### `/admin/attendance` Page (Permission: `attendance:view`)

**Daily Attendance Tab:**
- Date picker (defaults today), then Class → Section → Session selectors
- If already marked: show summary bar + table with edit capability
- If not marked: show student list with radio buttons (P/A/L/H/Leave) per student
- Quick actions: "Mark All Present", "Copy from previous day"
- Submit → POST → show confirmation with summary
- Notification status chip: "Absence notifications scheduled for 30 min"

**Reports Tab:**
- Date range + class/section filters
- Table: Student Name, Class-Sec, Total Days, Present, Absent, Late, Leave, Attendance%
- Color-coded: red < threshold, yellow moderate, green above threshold
- Export to Excel/PDF

**Low Attendance Alert Tab:**
- Auto-filter: students below threshold (from settings)
- Table with send-reminder button per student

**Monthly Sheet Tab:**
- Select month + section → Preview PDF inline → Download button

### `/admin/holidays` Page
- Annual calendar view with holidays marked
- Month grid showing working days vs holidays
- Add Holiday button → dialog (name, date, type, description)
- Bulk import from Excel

### Attendance Widget on Teacher's Dashboard
- My sections for today → quick mark attendance
- Quick stats: X absent out of Y in Section 10-A

### `frontend/src/api/attendance.ts`
```typescript
export const attendanceApi = {
  getSectionForDate: (sectionId: string, date: string, session: string) =>
    api.get(`/attendance/section/${sectionId}?date=${date}&session=${session}`),
  markAttendance: (sectionId: string, data: AttendanceMarkRequest) =>
    api.post(`/attendance/section/${sectionId}`, data),
  updateRecord: (id: string, data: AttendanceUpdateRequest) =>
    api.put(`/attendance/${id}`, data),
  getStudentSummary: (studentId: string, params: SummaryParams) =>
    api.get(`/attendance/student/${studentId}`, { params }),
  getReport: (params: AttendanceReportParams) =>
    api.get('/attendance/report', { params }),
  getLowAttendance: (yearId: string, threshold: number) =>
    api.get(`/attendance/low-attendance?year_id=${yearId}&threshold=${threshold}`),
  exportAttendance: (params: AttendanceReportParams) =>
    api.get('/attendance/export', { params, responseType: 'blob' }),
  getMonthlySheetPdf: (sectionId: string, month: number, year: number) =>
    api.get(`/attendance/section/${sectionId}/monthly-sheet?month=${month}&year=${year}`, { responseType: 'blob' }),
  listHolidays: (yearId: string) => api.get(`/holidays?year_id=${yearId}`),
  createHoliday: (data: HolidayCreate) => api.post('/holidays', data),
  deleteHoliday: (id: string) => api.delete(`/holidays/${id}`),
};
```

---

## 7.8 Celery Periodic Task (Beat Schedule)

```python
# celery_app.py — Beat schedule
celery.conf.beat_schedule = {
    'check-absence-notifications': {
        'task': 'app.tasks.attendance.check_and_send_absence_notifications',
        'schedule': crontab(minute='*/15'),  # every 15 min during school hours
    },
}

@celery.task(queue="notifications")
def check_and_send_absence_notifications():
    """
    For each school:
    1. Get absent_notify_delay_minutes from settings
    2. Find absences marked today where (now - marked_at) >= delay AND notification not yet sent
    3. Send SMS/WhatsApp to primary parent
    4. Mark notification as sent in notification_logs
    """
```

---

## 7.9 Tests

```python
async def test_mark_attendance_creates_session_and_entries(): ...  # two-table insert
async def test_cannot_mark_on_holiday(): ...
async def test_duplicate_mark_updates_existing(): ...
    # UNIQUE(section_id, date, session_type) on attendance_sessions
    # UNIQUE(session_id, student_id) on student_attendance
async def test_attendance_percentage_calculation(): ...
async def test_low_attendance_threshold_filter(): ...
async def test_biometric_csv_import(): ...
async def test_working_day_check(): ...                        # Sat/Sun if not in working_days → warn
async def test_is_holiday_check(): ...
async def test_staff_attendance_uses_timestamptz_check_in(): ...  # check_in/check_out are datetime, not time
```

---

## 7.10 Deliverables Checklist

- [ ] Daily attendance marking for a section (batch upsert)
- [ ] Support for multiple sessions (full_day / morning / afternoon) per school setting
- [ ] Edit individual attendance record
- [ ] Holidays CRUD with working-day check in marks
- [ ] Student attendance summary (date range) with % calculation
- [ ] Low attendance report filtering by threshold
- [ ] Class-level monthly attendance sheet PDF
- [ ] Absence notification Celery task (delayed after marking)
- [ ] Staff attendance marking (manual + biometric CSV import)
- [ ] Staff monthly attendance summary for payroll integration
- [ ] Attendance export to Excel
- [ ] Daily attendance widget for teachers on their dashboard
- [ ] Holiday calendar view in frontend
