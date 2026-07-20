# Feature Prompt 23 — PTM (Parent-Teacher Meeting) Scheduling

## Round: 4 of 4 — Advanced Features
## Prerequisites: Prompts 09 (Students), 10 (Staff)

---

## Objective

Implement Parent-Teacher Meeting (PTM) event creation, teacher slot management, parent appointment booking, and meeting feedback collection.

---

## 1. Database Models (`backend/app/models/ptm.py`)

```python
import uuid
from datetime import date
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin

class PTMEvent(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "ptm_events"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    event_date: Mapped[date] = mapped_column(nullable=False)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)  # "09:00"
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)    # "13:00"
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, default=10)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False)
    is_open_for_booking: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    slots: Mapped[list["PTMSlot"]] = relationship("PTMSlot", back_populates="event")


class PTMSlot(Base, TimestampMixin):
    __tablename__ = "ptm_slots"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("ptm_events.id", ondelete="CASCADE"), nullable=False)
    teacher_staff_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("staff.id"), nullable=False)
    slot_time: Mapped[str] = mapped_column(String(10), nullable=False)  # "09:00"
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)

    event: Mapped[PTMEvent] = relationship("PTMEvent", back_populates="slots")
    appointment: Mapped["PTMAppointment | None"] = relationship(
        "PTMAppointment", back_populates="slot", uselist=False)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("event_id", "teacher_staff_id", "slot_time", name="uq_ptm_slot"),
    )


class PTMAppointment(Base, TimestampMixin):
    __tablename__ = "ptm_appointments"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("ptm_slots.id"), nullable=False, unique=True)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("students.id"), nullable=False)
    parent_user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="booked")  # booked/attended/cancelled
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    teacher_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    slot: Mapped[PTMSlot] = relationship("PTMSlot", back_populates="appointment")
```

---

## 2. Alembic Migration

```sql
CREATE TABLE ptm_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    title VARCHAR(300) NOT NULL,
    event_date DATE NOT NULL,
    start_time VARCHAR(10) NOT NULL,
    end_time VARCHAR(10) NOT NULL,
    slot_duration_minutes INTEGER DEFAULT 10 NOT NULL,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    is_open_for_booking BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE ptm_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES ptm_events(id) ON DELETE CASCADE,
    teacher_staff_id UUID NOT NULL REFERENCES staff(id),
    slot_time VARCHAR(10) NOT NULL,
    is_booked BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_ptm_slot UNIQUE (event_id, teacher_staff_id, slot_time)
);

CREATE TABLE ptm_appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slot_id UUID NOT NULL UNIQUE REFERENCES ptm_slots(id),
    student_id UUID NOT NULL REFERENCES students(id),
    parent_user_id UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'booked' NOT NULL,
    feedback TEXT,
    teacher_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
```

---

## 3. Service

```python
async def create_ptm_event(db, school_id, data, current_user) -> PTMEvent:
    """Create PTM event and auto-generate slots for all teachers."""

async def generate_slots(db, event_id, staff_ids, school_id):
    """For each teacher, generate slots from start_time to end_time with slot_duration_minutes."""

async def book_appointment(db, slot_id, student_id, parent_user_id, school_id) -> PTMAppointment:
    """Check slot.is_booked=False. Book + set is_booked=True. Send confirmation."""

async def cancel_appointment(db, appointment_id, school_id, current_user):
    """Cancel + set slot.is_booked=False. Notify parent and teacher."""

async def get_teacher_schedule(db, event_id, staff_id) -> list:
    """All slots for teacher with booking details."""
```

---

## 4. API Endpoints

```
GET    /ptm-events                            → list PTM events                [ptm:view]
POST   /ptm-events                            → create PTM event              [ptm:create]
POST   /ptm-events/{id}/open                 → open for booking               [ptm:update]
GET    /ptm-events/{id}/slots?teacher_id=    → available slots                [ptm:view]
POST   /ptm-appointments                     → book appointment               [ptm:create]
DELETE /ptm-appointments/{id}                → cancel booking                 [ptm:update]
PUT    /ptm-appointments/{id}/teacher-notes  → add teacher notes              [ptm:update]
GET    /ptm-events/{id}/schedule             → full event schedule            [ptm:view]
```

---

## 5. Frontend

### PTM Page (`/ptm`)
- Event list with status badge (Open/Closed/Past)
- Create Event form with date/time/duration
- Per-event: teacher schedule grid

### Parent Booking View (in Parent Portal)
- Available teachers for upcoming PTM
- Book a slot (shows available times)
- My booked appointments

---

## Verification Checklist

- [ ] Slot generation covers full event time range in slot_duration_minutes intervals
- [ ] Booking validates slot.is_booked=False (race condition safe with DB transaction)
- [ ] Cancellation sets is_booked=False to free slot for rebooking
- [ ] `is_open_for_booking` must be True for parents to book
- [ ] Confirmation notification sent via notification engine
