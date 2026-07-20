# Feature Prompt 22 — Homework & Lesson Plans

## Round: 4 of 4 — Advanced Features
## Prerequisites: Prompts 06 (Classes/Subjects), 07 (Timetable)

---

## Objective

Implement homework assignment by teachers with student submissions tracking, and lesson plan creation with curriculum mapping. Includes parent visibility for homework.

---

## 1. Database Models (`backend/app/models/homework.py`)

```python
import uuid
from datetime import date
from sqlalchemy import String, Boolean, Date, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
import enum

class Homework(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "homework"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("classes.id"), nullable=False)
    section_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("sections.id"), nullable=True)  # None = all sections in class
    subject_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("subjects.id"), nullable=False)
    assigned_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    max_marks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attachments: Mapped[list] = mapped_column(JSONB, default=[])  # [{file_url, file_name}]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    submissions: Mapped[list["HomeworkSubmission"]] = relationship(
        "HomeworkSubmission", back_populates="homework")


class HomeworkSubmission(Base, TimestampMixin):
    __tablename__ = "homework_submissions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    homework_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("homework.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("students.id"), nullable=False)
    submitted_at: Mapped[str | None] = mapped_column(nullable=True)  # TIMESTAMPTZ
    is_late: Mapped[bool] = mapped_column(Boolean, default=False)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    marks_obtained: Mapped[int | None] = mapped_column(Integer, nullable=True)
    teacher_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/submitted/graded

    homework: Mapped[Homework] = relationship("Homework", back_populates="submissions")

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("homework_id", "student_id", name="uq_homework_submission"),
    )


class LessonPlan(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "lesson_plans"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("classes.id"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("subjects.id"), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    topic: Mapped[str] = mapped_column(String(300), nullable=False)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=45)
    objectives: Mapped[str | None] = mapped_column(Text, nullable=True)
    teaching_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    resources: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/approved
    approved_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

---

## 2. Alembic Migration

```sql
CREATE TABLE homework (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id),
    section_id UUID REFERENCES sections(id),
    subject_id UUID NOT NULL REFERENCES subjects(id),
    assigned_by UUID NOT NULL REFERENCES users(id),
    title VARCHAR(300) NOT NULL,
    description TEXT,
    assigned_date DATE NOT NULL,
    due_date DATE NOT NULL,
    max_marks INTEGER,
    attachments JSONB DEFAULT '[]' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_homework_school ON homework(school_id, due_date);
CREATE INDEX ix_homework_class ON homework(class_id, subject_id);

CREATE TABLE homework_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    homework_id UUID NOT NULL REFERENCES homework(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id),
    submitted_at TIMESTAMPTZ,
    is_late BOOLEAN DEFAULT FALSE NOT NULL,
    file_url VARCHAR(500),
    remarks TEXT,
    marks_obtained INTEGER,
    teacher_remarks TEXT,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_homework_submission UNIQUE (homework_id, student_id)
);

CREATE TABLE lesson_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    class_id UUID NOT NULL REFERENCES classes(id),
    subject_id UUID NOT NULL REFERENCES subjects(id),
    created_by UUID NOT NULL REFERENCES users(id),
    title VARCHAR(300) NOT NULL,
    topic VARCHAR(300) NOT NULL,
    plan_date DATE NOT NULL,
    duration_minutes INTEGER DEFAULT 45 NOT NULL,
    objectives TEXT,
    teaching_method TEXT,
    resources TEXT,
    evaluation_method TEXT,
    status VARCHAR(20) DEFAULT 'draft' NOT NULL,
    approved_by UUID,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
```

---

## 3. API Endpoints

```
# Homework
GET    /homework?class_id=&subject_id=&due=   → list homework                  [homework:view]
POST   /homework                              → create homework                [homework:create]
PUT    /homework/{id}                         → update homework                [homework:update]
DELETE /homework/{id}                         → delete homework                [homework:delete]

# Submissions
GET    /homework/{id}/submissions             → all submissions                [homework:view]
POST   /homework/{id}/submit                 → student submit                 [homework:create]
POST   /homework/{id}/grade/{student_id}     → teacher grade submission       [homework:update]

# Parent/Student view
GET    /homework/my?student_id=              → homework assigned to student   [auth]

# Lesson Plans
GET    /lesson-plans?class_id=&subject_id=   → list lesson plans              [homework:view]
POST   /lesson-plans                         → create lesson plan             [homework:create]
PUT    /lesson-plans/{id}                    → update lesson plan             [homework:update]
POST   /lesson-plans/{id}/approve            → HOD approves plan             [homework:update]
```

---

## 4. Frontend

### Homework Page (`/homework`)
- **Teacher view**: Create homework form; per-homework submission tracker (X/Y submitted, overdue)
- **Date range and subject filter**
- **Grading modal**: submission list with marks input

### Student/Parent Homework View
- Due today / upcoming / past homework list
- Submit button (file upload)
- Grades received

---

## Verification Checklist

- [ ] UNIQUE on (homework_id, student_id) for submissions
- [ ] `is_late` computed as `submitted_at > homework.due_date`
- [ ] Teacher can only create homework for sections where they are assigned subject teacher
- [ ] Parent API (`/homework/my`) requires parent-student link validation
- [ ] Lesson plan approval changes status from draft → approved
- [ ] Homework notification sent to parents on creation (via notification engine)
