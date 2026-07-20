# Feature Prompt 16 — Exam Management

## Round: 3 of 4 — Academic & Financial
## Prerequisites: Prompts 01–09 complete

---

## Objective

Implement complete exam lifecycle: exam type setup, grading scales, exam scheduling, mark entry by teachers, report card generation with grades, result publish/unpublish, admit card PDFs, and rank/merit list generation.

---

## 1. Database Models (`backend/app/models/exam.py`)

```python
import uuid
from datetime import date
from sqlalchemy import String, Boolean, Date, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
import enum

class ExamType(Base, TimestampMixin):
    __tablename__ = "exam_types"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)   # "Unit Test 1", "Quarterly"
    weight_percent: Mapped[float] = mapped_column(Float, default=100.0)  # % contribution to final
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class GradingScale(Base, TimestampMixin):
    __tablename__ = "grading_scales"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    ranges: Mapped[list] = mapped_column(JSONB, nullable=False)
    # ranges: [{"grade": "A+", "min": 90, "max": 100, "points": 10.0, "remark": "Outstanding"}]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Exam(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "exams"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False)
    exam_type_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("exam_types.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    grading_scale_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("grading_scales.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class ExamSchedule(Base, TimestampMixin):
    """Per-subject schedule for an exam."""
    __tablename__ = "exam_schedules"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("classes.id"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("subjects.id"), nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "09:00"
    end_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    max_marks: Mapped[float] = mapped_column(Float, default=100.0)
    passing_marks: Mapped[float] = mapped_column(Float, default=35.0)
    exam_room: Mapped[str | None] = mapped_column(String(100), nullable=True)

class StudentMark(Base, TimestampMixin):
    """Individual student mark for a subject exam."""
    # NOTE: Model is StudentMark (NOT ExamResult)
    __tablename__ = "student_marks"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    exam_schedule_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("exam_schedules.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    marks_obtained: Mapped[float | None] = mapped_column(Float, nullable=True)  # None = absent
    is_absent: Mapped[bool] = mapped_column(Boolean, default=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    entered_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("exam_schedule_id", "student_id", name="uq_student_mark"),
    )
```

---

## 2. Alembic Migration

```sql
CREATE TABLE exam_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    weight_percent FLOAT DEFAULT 100.0 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE grading_scales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    ranges JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE exams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    exam_type_id UUID NOT NULL REFERENCES exam_types(id),
    name VARCHAR(200) NOT NULL,
    start_date DATE,
    end_date DATE,
    is_published BOOLEAN DEFAULT FALSE NOT NULL,
    grading_scale_id UUID REFERENCES grading_scales(id),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE exam_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id),
    subject_id UUID NOT NULL REFERENCES subjects(id),
    exam_date DATE NOT NULL,
    start_time VARCHAR(10),
    end_time VARCHAR(10),
    max_marks FLOAT DEFAULT 100.0 NOT NULL,
    passing_marks FLOAT DEFAULT 35.0 NOT NULL,
    exam_room VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE student_marks (
    -- NOTE: table is student_marks (NOT exam_results)
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    exam_schedule_id UUID NOT NULL REFERENCES exam_schedules(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    marks_obtained FLOAT,
    is_absent BOOLEAN DEFAULT FALSE NOT NULL,
    remarks TEXT,
    entered_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_student_mark UNIQUE (exam_schedule_id, student_id)
);

CREATE INDEX ix_student_marks_exam ON student_marks(exam_id);
CREATE INDEX ix_student_marks_student ON student_marks(student_id);
```

---

## 3. Seed — Default Grading Scale

```python
DEFAULT_GRADING_SCALE = {
    "name": "Standard",
    "ranges": [
        {"grade": "A+", "min": 91, "max": 100, "points": 10.0, "remark": "Outstanding"},
        {"grade": "A",  "min": 81, "max": 90,  "points": 9.0,  "remark": "Excellent"},
        {"grade": "B+", "min": 71, "max": 80,  "points": 8.0,  "remark": "Very Good"},
        {"grade": "B",  "min": 61, "max": 70,  "points": 7.0,  "remark": "Good"},
        {"grade": "C+", "min": 51, "max": 60,  "points": 6.0,  "remark": "Average"},
        {"grade": "C",  "min": 41, "max": 50,  "points": 5.0,  "remark": "Below Average"},
        {"grade": "D",  "min": 35, "max": 40,  "points": 4.0,  "remark": "Passed"},
        {"grade": "F",  "min": 0,  "max": 34,  "points": 0.0,  "remark": "Failed"},
    ]
}
```

---

## 4. Service (`backend/app/services/exam_service.py`)

```python
def get_grade(marks: float, max_marks: float, scale_ranges: list) -> dict:
    """Calculate percentage, grade, points, remark from grading scale."""
    pct = (marks / max_marks) * 100
    for r in sorted(scale_ranges, key=lambda x: x["min"], reverse=True):
        if pct >= r["min"]:
            return {"grade": r["grade"], "points": r["points"], "remark": r["remark"], "pct": pct}
    return {"grade": "F", "points": 0, "remark": "Failed", "pct": pct}

async def enter_marks_bulk(db, exam_schedule_id, school_id, records: list, current_user):
    """
    Bulk upsert StudentMark records.
    Validate: exam not published, student enrolled in class.
    """

async def publish_exam(db, exam_id, school_id, current_user) -> Exam:
    """
    Validate all schedules have marks entered for all enrolled students.
    Set is_published=True.
    Send notification to parents.
    """

async def unpublish_exam(db, exam_id, school_id, current_user) -> Exam:
    """Revert to draft. Only principal can unpublish."""

async def generate_report_card(db, student_id, exam_id, school_id) -> bytes:
    """
    WeasyPrint report card:
    - School header
    - Student info (name, class, roll, admission_number)
    - Marks table: Subject | Max | Obtained | % | Grade
    - Total/Aggregate row
    - Attendance % for the term
    - Rank in class
    - Teacher/Principal signature section
    """

async def get_merit_list(db, exam_id, class_id, school_id) -> list:
    """
    Calculate total marks for each student in class.
    Sort by total descending.
    Return ranked list with grade.
    """

async def generate_admit_card_pdf(db, student_id, exam_id, school_id) -> bytes:
    """
    Admit card with:
    - Student photo + details
    - Exam schedule table (subject / date / time / room)
    - Instructions
    """
```

---

## 5. API Endpoints

```
# Exam Types & Grading
GET    /exam-types                           → list exam types                 [exams:view]
POST   /exam-types                           → create exam type               [exams:create]
GET    /grading-scales                       → list grading scales             [exams:view]
POST   /grading-scales                       → create grading scale           [exams:create]
POST   /grading-scales/seed-default          → seed default scale             [exams:create]

# Exams
GET    /exams?academic_year_id=              → list exams                      [exams:view]
POST   /exams                                → create exam                    [exams:create]
PUT    /exams/{id}                           → update exam                    [exams:update]
POST   /exams/{id}/publish                   → publish results                [exams:update]
POST   /exams/{id}/unpublish                 → unpublish results              [exams:update]

# Exam Schedules
GET    /exams/{id}/schedules                 → list schedules                 [exams:view]
POST   /exams/{id}/schedules                 → add schedule item              [exams:create]
PUT    /exams/{id}/schedules/{sid}           → update schedule                [exams:update]
DELETE /exams/{id}/schedules/{sid}           → delete schedule                [exams:delete]

# Marks Entry
GET    /exams/{id}/marks?class_id=           → view marks entry grid          [exams:view]
POST   /exam-schedules/{sid}/marks           → bulk enter marks               [exams:update]
GET    /exams/{id}/merit-list?class_id=      → class merit list               [exams:view]

# Report Cards & Admit Cards
GET    /students/{id}/report-card/{exam_id}  → download report card PDF       [exams:export]
GET    /students/{id}/admit-card/{exam_id}   → download admit card PDF        [exams:export]
GET    /exams/{id}/admit-cards/{class_id}    → bulk admit card PDF            [exams:export]
```

---

## 6. Frontend: Exam Pages

### Exams List Page (`/exams`)
- List of exams with status (Upcoming, In Progress, Published)
- Create Exam button
- Per exam: Schedule, Enter Marks, View Results, Publish/Unpublish

### Mark Entry Page (`/exams/:id/marks`)
- Class/Section/Subject selector
- Table: Roll No | Name | Max Marks | Obtained | Absent toggle | Grade (computed)
- Save + Submit for Review

### Results/Merit List Page
- Class/Section filter
- Rank table with student photos, total, % and grade
- Download Merit List PDF

### Report Card Page
- Student search
- Report card preview with print button

---

## 7. Custom Hooks

```typescript
export function useExams(yearId: string) { ... }
export function useMarkEntry(scheduleId: string) { ... }
export function useMeritList(examId: string, classId: string) { ... }
export function useStudentReportCard(studentId: string, examId: string) { ... }
```

---

## Verification Checklist

- [ ] Model named `StudentMark` and table named `student_marks` (NOT `exam_results`)
- [ ] UNIQUE constraint `uq_student_mark` on (exam_schedule_id, student_id)
- [ ] Grade calculation uses grading_scale.ranges correctly
- [ ] Publish validates all students have marks entered
- [ ] Unpublish only allowed by principal role
- [ ] Report card includes attendance % for the academic term
- [ ] Rank is computed per class (not overall school)
- [ ] Admit card PDF includes exam room from exam_schedules
- [ ] `weight_percent` on ExamType used in cumulative result calculations
- [ ] Mark entry blocked on published exams
