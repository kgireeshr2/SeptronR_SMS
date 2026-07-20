# Feature Prompt 24 — School Calendar

## Round: 4 of 4 — Advanced Features
## Prerequisites: Prompts 05 (Academic Year), 10 (Holidays)

---

## Objective

Implement a school-wide calendar with FullCalendar integration: events (holidays, exams, PTM, sports day), class-specific events, iCal export, and event notifications.

---

## 1. Database Models (`backend/app/models/calendar.py`)

```python
import uuid
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
import enum

class EventType(str, enum.Enum):
    HOLIDAY = "holiday"
    EXAM = "exam"
    PTM = "ptm"
    SPORTS = "sports"
    CULTURAL = "cultural"
    ACADEMIC = "academic"
    GENERAL = "general"

class CalendarEvent(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "calendar_events"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[EventType] = mapped_column(String(30), nullable=False)
    start_date: Mapped[str] = mapped_column(nullable=False)    # TIMESTAMPTZ
    end_date: Mapped[str] = mapped_column(nullable=False)      # TIMESTAMPTZ
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)  # hex color
    class_ids: Mapped[list] = mapped_column(JSONB, default=[])  # empty = school-wide
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Reference to source (e.g. holiday_id, exam_id, ptm_event_id)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
```

---

## 2. Alembic Migration

```sql
CREATE TABLE calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID REFERENCES academic_years(id),
    title VARCHAR(300) NOT NULL,
    description TEXT,
    event_type VARCHAR(30) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    is_all_day BOOLEAN DEFAULT TRUE NOT NULL,
    color VARCHAR(20),
    class_ids JSONB DEFAULT '[]' NOT NULL,
    location VARCHAR(200),
    is_public BOOLEAN DEFAULT TRUE NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    source_type VARCHAR(50),
    source_id UUID,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_calendar_events_school ON calendar_events(school_id, start_date);
```

---

## 3. Auto-Population

When holidays are created → auto-create CalendarEvent with event_type="holiday", source_type="holiday", source_id=holiday.id

When exams are created → auto-create CalendarEvent with event_type="exam", source_type="exam"

When PTM events are created → auto-create CalendarEvent with event_type="ptm"

---

## 4. Service

```python
async def get_calendar_events(db, school_id, start, end, class_ids=None) -> list:
    """Events in date range for school + optional class filter."""

async def generate_ical(db, school_id, academic_year_id) -> str:
    """Generate iCal (.ics) file content for all school events."""

async def notify_upcoming_events(db, school_id):
    """Celery Beat: notify 3 days before event."""
```

---

## 5. API Endpoints

```
GET    /calendar-events?start=&end=&class_id= → events in range              [academic_settings:view]
POST   /calendar-events                        → create event                 [academic_settings:create]
PUT    /calendar-events/{id}                   → update event                 [academic_settings:update]
DELETE /calendar-events/{id}                   → delete event                 [academic_settings:delete]
GET    /calendar-events/ical                   → download .ics file           [auth]
```

---

## 6. Frontend: Calendar Page (`/calendar`)

- **FullCalendar** month/week/day views
- Color-coded event types
- Click event → detail popover
- Add Event button (admin only)
- Filter by event type (holiday/exam/sports/etc.)
- Export to iCal button

---

## Verification Checklist

- [ ] Calendar auto-populated when holidays/exams/PTM created
- [ ] iCal export generates valid `.ics` content
- [ ] `class_ids=[]` means school-wide (visible to all)
- [ ] FullCalendar receives events in `{id, title, start, end, color}` format
- [ ] Event deletion (source event like holiday) cascades to calendar_event via source_id
