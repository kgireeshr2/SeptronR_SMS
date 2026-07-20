# Feature Prompt 07 — Timetable

## Round: 1 of 4 — Foundation
## Prerequisites: Prompts 01–06 complete

---

## Objective

Implement the timetable system: `timetable` table with teacher/room conflict detection, timetable grid view per section, teacher schedule view, drag-and-drop builder (dnd-kit), and PDF export.

---

## 1. Database Model (`backend/app/models/classes.py` — add to classes module)

```python
import uuid
from datetime import time
from sqlalchemy import String, Integer, ForeignKey, Time, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.models.base import Base, TimestampMixin

class Timetable(Base, TimestampMixin):
    __tablename__ = "timetable"   # NOTE: singular "timetable", not "timetables"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=Monday, 7=Sunday
    period_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, ...
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        # No two periods in same section on same day
        UniqueConstraint("section_id", "academic_year_id", "day_of_week", "period_number",
                         name="uq_timetable_slot"),
        # Teacher conflict index (checked by service layer, not DB constraint)
        Index("ix_timetable_teacher_slot", "teacher_id", "academic_year_id", "day_of_week", "period_number"),
        Index("ix_timetable_room_slot", "room_number", "school_id", "academic_year_id",
              "day_of_week", "period_number"),
    )
```

---

## 2. Alembic Migration

```sql
CREATE TABLE timetable (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES users(id),
    academic_year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL,  -- 1=Mon, 7=Sun
    period_number INTEGER NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room_number VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_timetable_slot UNIQUE (section_id, academic_year_id, day_of_week, period_number)
);

CREATE INDEX ix_timetable_section ON timetable(section_id, academic_year_id);
CREATE INDEX ix_timetable_teacher_slot ON timetable(teacher_id, academic_year_id, day_of_week, period_number);
CREATE INDEX ix_timetable_room_slot ON timetable(room_number, school_id, academic_year_id, day_of_week, period_number);
```

---

## 3. Pydantic Schemas

```python
from pydantic import BaseModel, model_validator
from uuid import UUID
from datetime import time

class TimetableSlotCreate(BaseModel):
    sectionId: UUID
    subjectId: UUID
    teacherId: UUID | None = None
    academicYearId: UUID
    dayOfWeek: int  # 1-7
    periodNumber: int
    startTime: time
    endTime: time
    roomNumber: str | None = None

    @model_validator(mode="after")
    def validate_day_and_time(self):
        if not 1 <= self.dayOfWeek <= 7:
            raise ValueError("dayOfWeek must be 1-7")
        if self.endTime <= self.startTime:
            raise ValueError("endTime must be after startTime")
        return self

class TimetableSlotUpdate(BaseModel):
    subjectId: UUID | None = None
    teacherId: UUID | None = None
    startTime: time | None = None
    endTime: time | None = None
    roomNumber: str | None = None

class TimetableSlotResponse(BaseModel):
    id: UUID
    sectionId: UUID
    subjectId: UUID
    subjectName: str
    subjectCode: str | None
    teacherId: UUID | None
    teacherName: str | None
    dayOfWeek: int
    periodNumber: int
    startTime: time
    endTime: time
    roomNumber: str | None
    model_config = {"from_attributes": True}

class TimetableGridResponse(BaseModel):
    """Grid structure: {day_of_week: {period_number: TimetableSlotResponse}}"""
    grid: dict[int, dict[int, TimetableSlotResponse | None]]
    days: list[int]
    periods: list[int]
    maxPeriods: int

class BulkTimetableCreate(BaseModel):
    sectionId: UUID
    academicYearId: UUID
    slots: list[TimetableSlotCreate]
```

---

## 4. Repository (`backend/app/repositories/timetable_repository.py`)

```python
async def get_timetable_for_section(db, section_id, academic_year_id) -> list[Timetable]: ...
async def get_timetable_slot(db, section_id, academic_year_id, day_of_week, period_number) -> Timetable | None: ...
async def create_slot(db, data: TimetableSlotCreate) -> Timetable: ...
async def update_slot(db, slot: Timetable, data: dict) -> Timetable: ...
async def delete_slot(db, slot: Timetable) -> None: ...
async def get_teacher_schedule(db, teacher_id, academic_year_id) -> list[Timetable]: ...
async def check_teacher_conflict(db, teacher_id, academic_year_id, day_of_week, period_number,
                                  exclude_slot_id=None) -> bool:
    """Return True if teacher already has a slot at this day+period (in any section)."""
    ...
async def check_room_conflict(db, school_id, room_number, academic_year_id, day_of_week,
                               period_number, exclude_slot_id=None) -> bool: ...
async def clear_section_timetable(db, section_id, academic_year_id) -> None: ...
async def bulk_create_slots(db, slots: list[TimetableSlotCreate]) -> list[Timetable]: ...
```

---

## 5. Service (`backend/app/services/timetable_service.py`)

```python
async def create_timetable_slot(db, school_id, data: TimetableSlotCreate, current_user) -> Timetable:
    """
    1. Validate year not locked.
    2. Check teacher conflict: same teacher, same year, same day, same period in ANY section.
       → Raise 409: "Teacher {name} is already scheduled at {day} period {n}"
    3. Check room conflict: same room_number, same school, same year, same day, same period.
       → Raise 409: "Room {room} is already occupied at {day} period {n}"
    4. Create slot. Audit log.
    """
    ...

async def update_timetable_slot(db, slot_id, school_id, data: TimetableSlotUpdate, current_user) -> Timetable:
    """
    Re-run conflict checks (exclude current slot_id).
    Update slot. Audit log.
    """
    ...

async def bulk_create_timetable(db, school_id, data: BulkTimetableCreate, current_user) -> dict:
    """
    Process each slot in sequence:
      - Run conflict checks
      - If conflict: add to errors list, skip
      - If OK: create slot
    Return {created: N, errors: [{slot_info, reason}]}
    """
    ...

async def get_section_timetable_grid(db, section_id, academic_year_id) -> TimetableGridResponse:
    """
    Fetch all slots for section.
    Build a nested dict: {day: {period: slot}}
    Compute maxPeriods = max period_number across all slots.
    """
    ...

async def generate_timetable_pdf(db, section_id, academic_year_id, school_id) -> bytes:
    """
    Fetch grid. Render Jinja2 HTML template timetable.html.
    WeasyPrint to PDF bytes.
    """
    ...
```

---

## 6. API Endpoints (`backend/app/api/v1/endpoints/timetable.py`)

```
GET    /timetable/section/{section_id}?year_id=   → timetable grid for section   [timetable:view]
POST   /timetable                                  → create single slot            [timetable:create]
PUT    /timetable/{slot_id}                        → update slot                   [timetable:update]
DELETE /timetable/{slot_id}                        → delete slot                   [timetable:delete]
POST   /timetable/bulk                             → bulk create slots             [timetable:create]
GET    /timetable/teacher/{teacher_id}?year_id=    → teacher's schedule            [timetable:view]
GET    /timetable/section/{section_id}/pdf?year_id= → download PDF                [timetable:export]
POST   /timetable/section/{section_id}/clear?year_id= → clear all slots in section [timetable:delete]
```

---

## 7. Jinja2 PDF Template (`backend/app/templates/timetable.html`)

Create an HTML template for the timetable PDF:
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Arial; font-size: 10px; }
    h1 { text-align: center; font-size: 14px; }
    h2 { text-align: center; font-size: 12px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #333; padding: 4px 6px; text-align: center; }
    th { background-color: #2563EB; color: white; }
    .empty { color: #ccc; }
  </style>
</head>
<body>
  <h1>{{ school_name }}</h1>
  <h2>Timetable — {{ class_name }} {{ section_name }} ({{ academic_year }})</h2>
  <table>
    <thead>
      <tr>
        <th>Period</th>
        {% for day in days %}<th>{{ day_names[day] }}</th>{% endfor %}
      </tr>
    </thead>
    <tbody>
      {% for period in periods %}
      <tr>
        <td>P{{ period }}</td>
        {% for day in days %}
          {% set slot = grid.get(day, {}).get(period) %}
          {% if slot %}
          <td>
            <strong>{{ slot.subjectCode or slot.subjectName }}</strong><br>
            <small>{{ slot.teacherName or '' }}</small><br>
            <small>{{ slot.startTime.strftime('%H:%M') }}–{{ slot.endTime.strftime('%H:%M') }}</small>
          </td>
          {% else %}
          <td class="empty">—</td>
          {% endif %}
        {% endfor %}
      </tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
```

---

## 8. Frontend: Types

```typescript
export interface TimetableSlot {
  id: string;
  sectionId: string;
  subjectId: string;
  subjectName: string;
  subjectCode?: string;
  teacherId?: string;
  teacherName?: string;
  dayOfWeek: number;
  periodNumber: number;
  startTime: string;
  endTime: string;
  roomNumber?: string;
}

export type TimetableGrid = Record<number, Record<number, TimetableSlot | null>>;

export const DAY_NAMES: Record<number, string> = {
  1: 'Monday', 2: 'Tuesday', 3: 'Wednesday',
  4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday',
};
```

---

## 9. Frontend: API Layer (`frontend/src/api/timetable.ts`)

```typescript
import api from './axios';

export const getSectionTimetableApi = async (sectionId: string, yearId: string) => {
  const res = await api.get<{ data: { grid: TimetableGrid; periods: number[] } }>(
    `/timetable/section/${sectionId}?year_id=${yearId}`
  );
  return res.data.data;
};

export const createTimetableSlotApi = async (data: Partial<TimetableSlot>) => {
  const res = await api.post<{ data: TimetableSlot }>('/timetable', data);
  return res.data.data;
};

export const updateTimetableSlotApi = async (id: string, data: Partial<TimetableSlot>) => {
  const res = await api.put<{ data: TimetableSlot }>(`/timetable/${id}`, data);
  return res.data.data;
};

export const deleteTimetableSlotApi = async (id: string) => api.delete(`/timetable/${id}`);

export const exportTimetablePdfApi = async (sectionId: string, yearId: string) => {
  const res = await api.get(`/timetable/section/${sectionId}/pdf?year_id=${yearId}`,
    { responseType: 'blob' });
  return res.data;
};
```

---

## 10. Frontend: Timetable Page (`frontend/src/pages/classes/TimetablePage.tsx`)

Route: `/timetable`

### Layout

1. **Filters**: Class selector → Section selector → Year (from Zustand store)
2. **Timetable Grid**: a `<table>` with rows = periods, columns = days (Mon–Sat)
   - Each cell shows: Subject name (bold), Teacher name (small), Time (small)
   - Empty cells show "+" button
   - Click any cell (filled or empty) → opens **Slot Editor dialog**
3. **Slot Editor Dialog**:
   - Subject dropdown (only subjects assigned to this class)
   - Teacher dropdown (auto-filtering to teacher assigned to that subject in class_subjects)
   - Start Time / End Time inputs
   - Room Number input
   - Period Number (readonly, derived from grid position)
   - Day of Week (readonly, derived from grid position)
   - Save → `createTimetableSlotApi` or `updateTimetableSlotApi`
   - If teacher conflict → toast error with conflict details
4. **"Export PDF"** button → triggers download
5. **dnd-kit Drag & Drop**: slots can be dragged from one cell to another
   - On drop: call `updateTimetableSlotApi` with new day_of_week and period_number
   - Re-run conflict check before confirming drop (optimistic update + rollback on error)

---

## 11. Sidebar Navigation

Add under "Academic" section:
- `Timetable` → `/timetable`

---

## Verification Checklist

- [ ] `POST /timetable` creates a slot; duplicate slot (same section + day + period) returns 409
- [ ] Teacher conflict: same teacher scheduled in two sections same day+period returns 409 with message
- [ ] Room conflict: same room double-booked same day+period returns 409
- [ ] `GET /timetable/section/{id}?year_id=X` returns full grid (nested day→period dict)
- [ ] `GET /timetable/section/{id}/pdf` returns downloadable PDF with rendered grid
- [ ] `GET /timetable/teacher/{id}?year_id=X` returns teacher's full week schedule
- [ ] Deleting a slot removes it; grid cell shows empty
- [ ] Frontend timetable grid renders all days × periods correctly
- [ ] Slot editor dialog populates dropdowns from class subjects
- [ ] dnd-kit drag-and-drop reorders slots and re-runs conflict check
