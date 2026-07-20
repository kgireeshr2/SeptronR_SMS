# Feature Prompt 28 — Dashboard

## Round: 4 of 4 — Advanced Features
## Prerequisites: All module data in place

---

## Objective

Implement 4 role-based dashboards (Admin, Teacher, Student, Parent) with real-time stats, charts (Recharts), and quick-action panels. Dashboard data cached in Redis for 2 minutes.

---

## 1. Backend Service (`backend/app/services/dashboard_service.py`)

```python
DASHBOARD_CACHE_TTL = 120  # 2 minutes

async def get_admin_dashboard(db, redis, school_id, academic_year_id) -> dict:
    """
    Redis key: dashboard:admin:{school_id}:{academic_year_id}
    TTL: 120 seconds

    Returns:
    {
      students: { total, enrolled, new_this_year, boys, girls },
      staff: { total, active, on_leave, absent_today },
      attendance: { today_pct, sections_marked, sections_total, monthly_trend: [12 months] },
      fees: { collected_paise, pending_paise, total_invoiced_paise, collection_rate },
      recent_admissions: [ last 5 ],
      pending_leaves: count,
      expiring_vehicles: count,
      low_stock_items: count,
      upcoming_exams: [ next 3 ],
      overdue_library: count,
    }
    """

async def get_teacher_dashboard(db, redis, school_id, staff_id, academic_year_id) -> dict:
    """
    Redis key: dashboard:teacher:{staff_id}:{academic_year_id}
    TTL: 120 seconds

    Returns:
    {
      my_sections: [ {class_name, section_name, student_count} ],
      today_timetable: [ {period, subject, section, time} ],
      attendance_today: { sections_marked, sections_total },
      pending_homework: count,
      recent_submissions: [ last 5 ],
      upcoming_exams: [ exams for my sections ],
    }
    """

async def get_student_dashboard(db, redis, school_id, student_id, academic_year_id) -> dict:
    """
    Redis key: dashboard:student:{student_id}
    TTL: 120 seconds

    Returns:
    {
      class: { name, section, roll_number },
      attendance: { present_days, absent_days, pct, month_calendar },
      pending_fees: { invoices: [...], total_paise },
      today_timetable: [ {period, subject, teacher, time} ],
      pending_homework: count,
      recent_marks: [ last 5 exams ],
      library: { issued_books, due_soon },
    }
    """

async def get_parent_dashboard(db, redis, school_id, parent_user_id) -> dict:
    """
    Redis key: dashboard:parent:{parent_user_id}
    TTL: 120 seconds
    Aggregate for all linked students.
    """
```

---

## 2. API Endpoints

```
GET    /dashboard/admin?year_id=              → admin dashboard data          [dashboard:view]
GET    /dashboard/teacher?year_id=            → teacher dashboard             [dashboard:view]
GET    /dashboard/student?year_id=            → student dashboard             [dashboard:view]
GET    /dashboard/parent                      → parent dashboard              [dashboard:view]
POST   /dashboard/refresh                     → invalidate Redis cache        [dashboard:view]
```

The endpoint auto-determines which dashboard based on current user's primary role.

`GET /dashboard` → detects role → redirects to appropriate dashboard endpoint.

---

## 3. Frontend: Dashboard Pages

### Admin Dashboard (`/dashboard`)

**Row 1 — KPI Cards (4 cards)**:
- Total Students (with trend arrow)
- Staff Present Today
- Fee Collection Rate %
- Pending Approvals (leave + admissions)

**Row 2 — Charts**:
- Attendance Trend: Line chart (12 months)
- Fee Collection: Bar chart (monthly collected vs invoiced)

**Row 3 — Tables**:
- Recent Admissions table (last 5)
- Pending Leave Requests (action buttons inline)
- Upcoming Exams (next 3)

**Row 4 — Alerts**:
- Low Stock Items alert card
- Expiring Vehicle Documents
- Overdue Library Books

### Teacher Dashboard
- Today's timetable timeline
- Attendance status per section
- Pending homework to grade
- Recent student performance

### Student Dashboard
- Attendance % gauge chart
- Today's timetable
- Fee dues card
- Pending homework list
- Recent exam marks

### Parent Dashboard
- Per-child tabs
- Attendance % for each child
- Fee dues
- Recent notifications

---

## 4. Custom Hooks

```typescript
// hooks/useDashboard.ts
export function useAdminDashboard(yearId: string) {
  return useQuery({
    queryKey: ['dashboard', 'admin', yearId],
    queryFn: () => api.get(`/dashboard/admin?year_id=${yearId}`),
    staleTime: 2 * 60 * 1000,  // match Redis TTL
    refetchInterval: 2 * 60 * 1000,
  });
}
```

---

## Verification Checklist

- [ ] Redis cache with TTL=120s for each dashboard type
- [ ] Cache key includes academic_year_id for invalidation
- [ ] `POST /dashboard/refresh` deletes Redis key for current user's dashboard
- [ ] Admin dashboard visible only to admin/principal roles
- [ ] Attendance trend uses 12-month lookback
- [ ] Fee collection rate = total_collected / total_invoiced × 100
- [ ] Parent dashboard aggregates data for all linked students
- [ ] Teacher dashboard only shows sections/timetable for that teacher's assignments
- [ ] Charts use Recharts components (not third-party chart libs)
