# PHASE 16 — CALENDAR MANAGEMENT

## Pre-Requisite
Phases 1–15 complete. Academic year, exams, holidays, PTM, homework all exist.

## Objective
Unified school calendar: events, holidays, exam schedules, homework due dates, PTM, and staff leave — all in a single calendar view with event creation, editing, and subscription (iCal export).

---

## 16.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 21: Calendar
calendar_events (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    title VARCHAR(300) NOT NULL, description TEXT,
    event_type calendar_event_type,  -- ⚠️ ENUM type (not VARCHAR)
        -- ENUM values: holiday|exam|meeting|sports|cultural|trip|other
        -- NOTE: 'ptm' and 'homework_due' are NOT calendar_event_type values;
        --       PTM and homework are synced from their respective tables.
    start_datetime TIMESTAMPTZ, end_datetime TIMESTAMPTZ,
    all_day BOOL DEFAULT FALSE,
    location VARCHAR(300),
    color_tag VARCHAR(20),            -- ⚠️ 'color_tag' not 'color'
    audience VARCHAR(20) DEFAULT 'all',  -- ⚠️ 'audience' not 'visibility'
        -- all|staff_only|students|parents
    audience_filter JSONB DEFAULT '{}', -- {class_ids: [...], section_ids: [...]}
    created_by UUID FK→users,
    created_at, updated_at,
    is_active BOOL DEFAULT TRUE,
    recurrence_rule TEXT            -- iCal RRULE
)
-- ⚠️ NO event_attendees table in actual schema.
-- If invite/RSVP tracking per user is needed, it must be added via Alembic migration.
-- Remove all event_attendees references from code.
```

> **Schema note**: The `event_type` is an ENUM `calendar_event_type` with values `holiday|exam|meeting|sports|cultural|trip|other` — NOT `ptm`, `homework_due`, or `custom`. The field for visibility is `audience` (not `visibility`). For a color-coded event, use `color_tag`. There is no `event_attendees` table.


---

## 16.2 Pydantic Schemas

```python
class CalendarEventCreate(BaseModel):
    title: str; description: Optional[str]
    event_type: str = "other"   # holiday|exam|meeting|sports|cultural|trip|other
    start_datetime: datetime; end_datetime: datetime
    all_day: bool = False
    location: Optional[str]
    color_tag: Optional[str]      # ⚠️ 'color_tag' not 'color'
    audience: str = "all"         # ⚠️ 'audience' not 'visibility'
    audience_filter: Optional[dict] = {}  # {class_ids:[...], section_ids:[...]}
    academic_year_id: UUID
    recurrence_rule: Optional[str]
    # ⚠️ No invite_user_ids (no event_attendees table)

class CalendarEventResponse(BaseModel):
    id: UUID; title: str; description: Optional[str]
    event_type: str; start_datetime: datetime; end_datetime: datetime
    all_day: bool; location: Optional[str]
    color_tag: Optional[str]    # ⚠️ 'color_tag'
    audience: str               # ⚠️ 'audience'
    audience_filter: Optional[dict]
    created_by_name: Optional[str]; is_active: bool

class CalendarQueryParams(BaseModel):
    from_date: date; to_date: date
    event_types: Optional[List[str]]
    academic_year_id: Optional[UUID]
    include: Optional[str] = "all"  # all|holidays|exams|homework|ptm|custom
```

---

## 16.3 Service Layer

```python
async def get_calendar_events(school_id: str, user_id: str, user_roles: list, params: CalendarQueryParams) -> List[CalendarEventResponse]:
    """
    1. Fetch calendar_events in date range for school
    2. Filter by visibility based on user role
    3. Also synthesize events from:
       - holidays table (event_type=holiday)
       - exams.start_date/end_date (event_type=exam)
       - exam_schedules per date (event_type=exam_schedule)
       - homework.due_date (event_type=homework_due)
       - ptm_schedules.ptm_date (event_type=ptm)
       - approved staff_leaves (staff_only)
    4. Merge and return sorted by start_datetime
    """

async def sync_academic_events_to_calendar(school_id: str, year_id: str) -> int:
    """Create/update calendar_events for all exams, holidays, PTMs for year."""

async def export_ical(school_id: str, user_id: str, from_date: date, to_date: date) -> str:
    """Generate iCal (.ics) string for all events user can see."""
```

---

## 16.4 API Endpoints

```
GET  /api/v1/calendar                    → list events in date range [calendar:view]
POST /api/v1/calendar                    → create event [calendar:create]
GET  /api/v1/calendar/{id}              → event detail
PUT  /api/v1/calendar/{id}              → update [calendar:update]
DELETE /api/v1/calendar/{id}            → delete [calendar:delete]
POST /api/v1/calendar/sync              → sync from exams/holidays/PTMs [calendar:manage]
GET  /api/v1/calendar/export/ical       → download .ics file [calendar:view]
# ⚠️ No /calendar/{id}/respond endpoint (no event_attendees table)
```

---

## 16.5 Frontend Pages

### `/admin/calendar` Page (Permission: `calendar:view`)
- Full calendar view (month/week/day) using `@fullcalendar/react` or `react-big-calendar`
- Color-coded by event_type:
  - holiday: red
  - exam: purple
  - ptm: blue
  - homework_due: orange
  - custom: user-chosen color
- Click date → create event dialog
- Click event → view/edit/delete dialog
- Filter checkboxes: show/hide event types
- "Sync from modules" button → calls sync endpoint
- Export iCal button → download .ics

### Parent/Student Calendar View (`/parent/calendar`, `/student/calendar`)
- Read-only calendar with visibility=all events
- + homework_due for their class/section

### `frontend/src/api/calendar.ts`
```typescript
export const calendarApi = {
  getEvents: (params: CalendarQueryParams) => api.get('/calendar', { params }),
  createEvent: (data: CalendarEventCreate) => api.post('/calendar', data),
  updateEvent: (id: string, data: Partial<CalendarEventCreate>) => api.put(`/calendar/${id}`, data),
  deleteEvent: (id: string) => api.delete(`/calendar/${id}`),
  syncFromModules: (yearId: string) => api.post('/calendar/sync', { academic_year_id: yearId }),
  exportIcal: (from: string, to: string) =>
    api.get(`/calendar/export/ical?from=${from}&to=${to}`, { responseType: 'blob' }),
};
```

---

## 16.6 iCal Export Generator (`backend/app/utils/ical_generator.py`)

```python
from icalendar import Calendar, Event
from datetime import datetime
import pytz

def generate_ical(events: List[dict], school_name: str, timezone: str) -> str:
    cal = Calendar()
    cal.add('prodid', f'-//{school_name}//School Calendar//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('x-wr-calname', f'{school_name} Calendar')
    cal.add('x-wr-timezone', timezone)
    tz = pytz.timezone(timezone)
    for ev in events:
        ie = Event()
        ie.add('summary', ev['title'])
        ie.add('dtstart', ev['start_datetime'].astimezone(tz))
        ie.add('dtend', ev['end_datetime'].astimezone(tz))
        ie.add('description', ev.get('description', ''))
        ie.add('location', ev.get('location', ''))
        ie.add('uid', str(ev['id']))
        cal.add_component(ie)
    return cal.to_ical().decode('utf-8')
```

---

## 16.7 Tests

```python
async def test_calendar_events_in_range(): ...
async def test_visibility_filter_staff_only(): ...     # parent cannot see staff_only events
async def test_sync_creates_exam_events(): ...
async def test_ical_export_valid_format(): ...
async def test_create_recurring_event(): ...
```

---

## 16.8 Deliverables Checklist

- [ ] Calendar event CRUD with event types and visibility levels
- [ ] Get events endpoint merges from multiple sources (exams, holidays, homework, PTM)
- [ ] Sync endpoint creates/updates calendar_events from all modules
- [ ] iCal (.ics) export (install `icalendar` package)
- [ ] Frontend calendar with @fullcalendar/react (install it)
- [ ] Color-coded event types
- [ ] Filter by event type checkboxes
- [ ] Click-to-create and click-to-edit event dialogs
- [ ] Parent/student read-only calendar with role-appropriate events
