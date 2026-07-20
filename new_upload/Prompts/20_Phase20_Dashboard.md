# PHASE 20 — DASHBOARD & CHARTS

## Pre-Requisite
Phases 1–19 complete. All modules implemented so dashboard can aggregate real data.

## Objective
Role-aware dashboards with KPI cards, charts (recharts), quick actions, and real-time widgets. Separate dashboards for: Admin, Teacher, Student, Parent, and Super Admin.

---

## 20.1 Dashboard API Design

One aggregate endpoint per dashboard type returns all widgets in a single request to minimize round trips.

### Backend: `backend/app/api/v1/dashboard.py`

```python
@router.get("/dashboard/admin")
async def admin_dashboard(
    year_id: UUID = Query(...),
    current_user = Depends(get_current_user),
    school_id = Depends(get_current_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Return all admin dashboard data in one response."""
```

---

## 20.2 Admin Dashboard Data Model

```python
class AdminDashboardResponse(BaseModel):
    # KPI Cards
    total_students: int
    total_staff: int
    total_fee_collected_this_month: int   # paise
    total_fee_outstanding: int            # paise
    total_present_today: int
    total_absent_today: int
    attendance_pct_today: float
    pending_leave_requests: int

    # Charts data
    monthly_fee_collection: List[MonthlyAmount]    # last 6 months
    attendance_trend: List[DayAttendance]           # last 30 days
    student_by_class: List[ClassStudentCount]
    student_by_gender: GenderBreakdown             # {male, female, other}
    fee_due_by_category: List[CategoryAmount]
    expense_vs_income: List[MonthlyFinancials]     # last 6 months

    # Tables
    recent_admissions: List[AdmissionSummary]      # last 5
    fee_defaulters_count: int
    upcoming_events: List[CalendarEventSummary]    # next 7 days
    low_stock_alerts: List[dict]
    expiring_vehicle_docs: List[dict]
    pending_leave_requests_list: List[dict]        # top 5 pending

class MonthlyAmount(BaseModel):
    month: str   # "Jan 2025"
    amount: int  # paise

class DayAttendance(BaseModel):
    date: str
    present: int; absent: int; total: int; pct: float
```

---

## 20.3 Teacher Dashboard Data Model

```python
class TeacherDashboardResponse(BaseModel):
    my_sections: List[SectionSummary]          # sections I'm class teacher of
    my_subjects: List[SubjectTeacherAssignment] # all class-subject I teach
    today_timetable: List[TimetableEntryResponse]  # my classes today
    pending_homework_reviews: int              # submissions awaiting review
    upcoming_exams: List[ExamSummary]          # in next 14 days
    my_leave_balance: List[LeaveBalanceSummary]
    today_attendance_marked: List[SectionAttendanceStatus]  # per section: marked?
    notifications: List[InAppNotificationResponse]  # last 5
```

---

## 20.4 Student Dashboard Data Model

```python
class StudentDashboardResponse(BaseModel):
    student_info: StudentResponse
    current_enrollment: EnrollmentSummary
    attendance_summary: StudentAttendanceSummary  # current month
    fee_dues: List[StudentFeeDetail]              # unpaid/partial fees
    pending_homework: List[HomeworkSummary]       # due_date >= today, not submitted
    upcoming_exams: List[ExamScheduleSummary]     # next 14 days
    recent_results: List[ExamResultSummary]       # last exam marks
    library_issued: List[LibraryIssueSummary]     # current loans
    notifications: List[InAppNotificationResponse]
```

---

## 20.5 Parent Dashboard Data Model

```python
class ParentDashboardResponse(BaseModel):
    children: List[ChildSummary]    # for each linked student
    # For primary child (or all if multiple):
    attendance_this_month: List[AttendanceSummaryPerChild]
    fee_summary: List[ChildFeeSummary]
    upcoming_ptm: Optional[PTMSlotResponse]
    recent_results: List[dict]
    notifications: List[InAppNotificationResponse]
    upcoming_events: List[CalendarEventSummary]

class ChildSummary(BaseModel):
    student_id: UUID; student_name: str
    class_name: str; section_name: str; photo_url: Optional[str]
    attendance_pct_this_month: float
    total_fee_due: int
```

---

## 20.6 Service Layer

```python
# backend/app/services/dashboard_service.py

async def get_admin_dashboard(school_id: str, year_id: str, db: AsyncSession) -> AdminDashboardResponse:
    """
    Run all sub-queries concurrently using asyncio.gather():
    - student counts, staff counts, fee totals, attendance today
    - chart data queries
    - recent records
    Merge and return.
    """
    results = await asyncio.gather(
        student_repo.count_by_section(school_id, year_id),
        staff_repo.count_active(school_id),
        fee_repo.monthly_collection(school_id, year_id, now.month, now.year),
        attendance_repo.count_absent_today(school_id, today),
        # ...etc
    )

async def get_teacher_dashboard(school_id: str, teacher_user_id: str, year_id: str) -> TeacherDashboardResponse: ...
async def get_student_dashboard(school_id: str, student_id: str, year_id: str) -> StudentDashboardResponse: ...
async def get_parent_dashboard(school_id: str, parent_user_id: str, year_id: str) -> ParentDashboardResponse: ...
```

---

## 20.7 API Endpoints

```
GET /api/v1/dashboard/admin    → admin dashboard [dashboard:view]
    ?year_id=UUID
GET /api/v1/dashboard/teacher  → teacher dashboard [authenticated]
    ?year_id=UUID
GET /api/v1/dashboard/student  → student dashboard [authenticated]
    ?student_id=UUID&year_id=UUID
GET /api/v1/dashboard/parent   → parent dashboard [authenticated]
    ?year_id=UUID
```

---

## 20.8 Frontend Dashboard Pages

### `/admin/dashboard` (default landing for admin roles)

Using `recharts` library (already in package.json).

**Layout: 2-3 column grid**

Row 1 — KPI Cards (6 cards):
```
Total Students | Total Staff | Fee Collected (Month) | Fee Outstanding | Present Today | Absent Today
```

Row 2 — Charts (2 columns):
```
[Monthly Fee Collection — Bar Chart]  |  [Attendance Trend — Line Chart]
```

Row 3 — Charts (2 columns):
```
[Students by Class — Bar Chart]  |  [Gender Breakdown — Pie Chart]
```

Row 4 — Tables (3 columns):
```
[Recent Admissions table]  |  [Pending Leave Requests]  |  [Upcoming Events]
```

Row 5 — Alerts (2 columns):
```
[Low Stock Alerts]  |  [Expiring Vehicle Documents]
```

### `/teacher/dashboard`
- Today's timetable as a card list
- "Mark Attendance" quick buttons per section (redirects to attendance page)
- Pending homework reviews count badge
- Leave balance mini-table

### `/student/dashboard`
- Attendance this month mini circular chart
- Pending homework cards
- Fee dues if any (with Pay button if online payment enabled)
- Upcoming exam cards

### `/parent/dashboard`
- Child selector tabs (if multiple children)
- Attendance card per child
- Fee summary per child
- Upcoming PTM notification card

### Dashboard Component Library (`frontend/src/components/dashboard/`)
```
KPICard.tsx         — icon + value + label + trend arrow
BarChart.tsx        — wrapper around recharts BarChart
LineChart.tsx       — wrapper around recharts LineChart
PieChart.tsx        — wrapper around recharts PieChart + legend
StatTable.tsx       — compact table for quick lists
AlertBadge.tsx      — amber/red alert cards for warnings
```

### `frontend/src/api/dashboard.ts`
```typescript
export const dashboardApi = {
  getAdmin: (yearId: string) => api.get(`/dashboard/admin?year_id=${yearId}`),
  getTeacher: (yearId: string) => api.get(`/dashboard/teacher?year_id=${yearId}`),
  getStudent: (studentId: string, yearId: string) =>
    api.get(`/dashboard/student?student_id=${studentId}&year_id=${yearId}`),
  getParent: (yearId: string) => api.get(`/dashboard/parent?year_id=${yearId}`),
};
```

---

## 20.9 Performance Optimization

1. Use `asyncio.gather()` for all concurrent DB queries in dashboard service.
2. Cache admin dashboard response in Redis for 2 minutes:
   `dashboard:admin:{school_id}:{year_id}` — TTL 120s
3. Cache teacher dashboard for 60s.
4. Student/parent dashboards: no cache (personalized, must be real-time).
5. Use `React.Suspense` + skeleton loading states for each chart section independently.

---

## 20.10 Tests

```python
async def test_admin_dashboard_returns_all_fields(): ...
async def test_admin_dashboard_cached(): ...              # second call uses cache
async def test_teacher_dashboard_own_sections_only(): ...  # doesn't leak other school's data
async def test_parent_dashboard_own_children_only(): ...
async def test_dashboard_zero_fill_empty_months(): ...     # months with no fee show 0, not missing
```

---

## 20.11 Deliverables Checklist

- [ ] Admin dashboard aggregate endpoint with all KPIs and chart data
- [ ] Teacher dashboard with timetable, pending homework, leave balance
- [ ] Student dashboard with attendance, pending homework, fee dues, exams
- [ ] Parent dashboard with child summaries, upcoming PTM
- [ ] All sub-queries run concurrently via `asyncio.gather()`
- [ ] Redis caching for admin/teacher dashboards (2min / 60s TTL)
- [ ] KPI card components with trend arrows
- [ ] Bar, Line, and Pie charts using recharts
- [ ] Monthly fee collection bar chart (last 6 months)
- [ ] Attendance trend line chart (last 30 days)
- [ ] Skeleton loading states for all dashboard sections
- [ ] Low stock and expiring document alert rows
