# Feature Prompt 06 — Classes, Sections & Subjects

## Round: 1 of 4 — Foundation
## Prerequisites: Prompts 01–05 complete

---

## Objective

Implement class management (`classes`), section management (`sections`), subject catalog (`subjects`), and class-subject teacher assignments (`class_subjects`). These form the academic structure that every operational module (attendance, exams, fees, etc.) references.

---

## 1. Database Models (`backend/app/models/classes.py`)

```python
import uuid
from sqlalchemy import String, Boolean, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.models.base import Base, TimestampMixin, SoftDeleteMixin

class Class(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # "Grade 1", "Class 10A"
    numeric_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # for sorting 1-12
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sections: Mapped[list["Section"]] = relationship("Section", back_populates="class_",
                                                      cascade="all, delete-orphan")
    class_subjects: Mapped[list["ClassSubject"]] = relationship("ClassSubject",
                                                                  back_populates="class_")

    __table_args__ = (
        UniqueConstraint("school_id", "academic_year_id", "name", name="uq_class_school_year_name"),
    )


class Section(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "sections"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)  # "A", "B", "Rose"
    capacity: Mapped[int] = mapped_column(Integer, default=40, nullable=False)
    class_teacher_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=True)
    room_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    class_: Mapped[Class] = relationship("Class", back_populates="sections")

    __table_args__ = (
        UniqueConstraint("class_id", "name", name="uq_section_class_name"),
    )


class Subject(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    full_marks: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    pass_marks: Mapped[int] = mapped_column(Integer, default=35, nullable=False)
    is_elective: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_subject_school_code"),
    )


class ClassSubject(Base, TimestampMixin):
    """Links a subject to a class for a given year, with an assigned teacher."""
    __tablename__ = "class_subjects"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    class_: Mapped[Class] = relationship("Class", back_populates="class_subjects")

    __table_args__ = (
        UniqueConstraint("class_id", "subject_id", name="uq_class_subject"),
    )
```

---

## 2. Alembic Migration

```sql
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    numeric_level INTEGER,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_class_school_year_name UNIQUE (school_id, academic_year_id, name)
);

CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(20) NOT NULL,
    capacity INTEGER DEFAULT 40 NOT NULL,
    class_teacher_id UUID REFERENCES users(id),
    room_number VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_section_class_name UNIQUE (class_id, name)
);

CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    full_marks INTEGER DEFAULT 100 NOT NULL,
    pass_marks INTEGER DEFAULT 35 NOT NULL,
    is_elective BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_subject_school_code UNIQUE (school_id, code)
);

CREATE TABLE class_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_class_subject UNIQUE (class_id, subject_id)
);
```

---

## 3. Pydantic Schemas

```python
class ClassCreate(BaseModel):
    name: str
    numericLevel: int | None = None
    academicYearId: UUID

class ClassUpdate(BaseModel):
    name: str | None = None
    numericLevel: int | None = None

class ClassResponse(BaseModel):
    id: UUID
    name: str
    numericLevel: int | None
    academicYearId: UUID
    sectionCount: int = 0
    isActive: bool
    model_config = {"from_attributes": True}

class SectionCreate(BaseModel):
    name: str
    capacity: int = 40
    classTeacherId: UUID | None = None
    roomNumber: str | None = None

class SectionUpdate(BaseModel):
    name: str | None = None
    capacity: int | None = None
    classTeacherId: UUID | None = None
    roomNumber: str | None = None

class SectionResponse(BaseModel):
    id: UUID
    classId: UUID
    name: str
    capacity: int
    classTeacherId: UUID | None
    classTeacherName: str | None = None
    roomNumber: str | None
    studentCount: int = 0
    isActive: bool
    model_config = {"from_attributes": True}

class SubjectCreate(BaseModel):
    name: str
    code: str | None = None
    fullMarks: int = 100
    passMarks: int = 35
    isElective: bool = False

class SubjectResponse(BaseModel):
    id: UUID
    name: str
    code: str | None
    fullMarks: int
    passMarks: int
    isElective: bool
    isActive: bool
    model_config = {"from_attributes": True}

class ClassSubjectAssign(BaseModel):
    subjectIds: list[UUID]  # list to assign (replaces all current)
    teacherAssignments: dict[str, UUID | None] = {}  # {subject_id: teacher_id}

class ClassSubjectResponse(BaseModel):
    id: UUID
    classId: UUID
    subjectId: UUID
    subjectName: str
    subjectCode: str | None
    teacherId: UUID | None
    teacherName: str | None
    model_config = {"from_attributes": True}
```

---

## 4. Repository (`backend/app/repositories/class_repository.py`)

```python
async def get_classes(db, school_id, academic_year_id) -> list[Class]: ...
async def get_class_by_id(db, class_id, school_id) -> Class | None: ...
async def create_class(db, school_id, academic_year_id, data: ClassCreate) -> Class: ...
async def update_class(db, class_: Class, data: dict) -> Class: ...
async def soft_delete_class(db, class_: Class, deleted_by: UUID) -> None: ...

async def get_sections(db, class_id) -> list[Section]: ...
async def get_section_by_id(db, section_id, school_id) -> Section | None: ...
async def create_section(db, class_id, school_id, data: SectionCreate) -> Section: ...
async def update_section(db, section: Section, data: dict) -> Section: ...
async def soft_delete_section(db, section: Section, deleted_by: UUID) -> None: ...
async def get_sections_by_school(db, school_id, academic_year_id) -> list[Section]: ...

async def get_subjects(db, school_id) -> list[Subject]: ...
async def create_subject(db, school_id, data: SubjectCreate) -> Subject: ...
async def update_subject(db, subject: Subject, data: dict) -> Subject: ...

async def get_class_subjects(db, class_id) -> list[ClassSubject]: ...
async def assign_subjects_to_class(db, class_id, assignments: list[dict]) -> None:
    """Bulk upsert class_subjects. Remove any not in the new list."""
    ...
async def get_subjects_for_section(db, section_id) -> list[Subject]:
    """Via section → class → class_subjects → subjects."""
    ...
```

---

## 5. Service (`backend/app/services/class_service.py`)

```python
async def create_class(db, school_id, data: ClassCreate, current_user) -> Class:
    """Validate year not locked. Unique name per year. Audit log."""
    ...

async def create_section(db, class_id, school_id, data: SectionCreate, current_user) -> Section:
    """Unique name per class. Validate class_teacher_id is a teacher role user. Audit log."""
    ...

async def assign_subjects(db, class_id, school_id, data: ClassSubjectAssign, current_user):
    """
    For each subjectId in the list:
      - Upsert ClassSubject(class_id, subject_id, teacher_id)
    Remove ClassSubjects not in the new list.
    Audit log.
    """
    ...

async def duplicate_class_structure(db, school_id, from_year_id, to_year_id, current_user):
    """
    Copy all classes + sections from one academic year to another.
    Does NOT copy enrollments or timetable.
    Returns summary: {classes_created: N, sections_created: N}
    """
    ...
```

---

## 6. API Endpoints

```
# Classes
GET    /classes?year_id={id}                → list classes for year    [classes:view]
POST   /classes                             → create class             [classes:create]
GET    /classes/{id}                        → get class with sections  [classes:view]
PUT    /classes/{id}                        → update class             [classes:update]
DELETE /classes/{id}                        → soft delete              [classes:delete]
POST   /classes/duplicate                   → copy structure to year   [classes:manage]

# Sections
GET    /classes/{class_id}/sections         → list sections            [classes:view]
POST   /classes/{class_id}/sections         → create section           [classes:create]
PUT    /sections/{id}                       → update section           [classes:update]
DELETE /sections/{id}                       → soft delete              [classes:delete]

# Subjects
GET    /subjects                            → list all subjects for school  [subjects:view]
POST   /subjects                            → create subject               [subjects:create]
PUT    /subjects/{id}                       → update subject               [subjects:update]
DELETE /subjects/{id}                       → soft delete                  [subjects:delete]

# Class-Subject Assignments
GET    /classes/{id}/subjects               → subjects assigned to class   [classes:view]
PUT    /classes/{id}/subjects               → bulk assign subjects         [classes:update]
```

---

## 7. Frontend: Types

```typescript
export interface Class {
  id: string;
  name: string;
  numericLevel?: number;
  academicYearId: string;
  sectionCount: number;
  isActive: boolean;
}

export interface Section {
  id: string;
  classId: string;
  name: string;
  capacity: number;
  classTeacherId?: string;
  classTeacherName?: string;
  roomNumber?: string;
  studentCount: number;
  isActive: boolean;
}

export interface Subject {
  id: string;
  name: string;
  code?: string;
  fullMarks: number;
  passMarks: number;
  isElective: boolean;
  isActive: boolean;
}

export interface ClassSubject {
  id: string;
  classId: string;
  subjectId: string;
  subjectName: string;
  subjectCode?: string;
  teacherId?: string;
  teacherName?: string;
}
```

---

## 8. Frontend: API Layer (`frontend/src/api/classes.ts`)

```typescript
import api from './axios';

export const getClassesApi = async (yearId: string) => {
  const res = await api.get<{ data: Class[] }>(`/classes?year_id=${yearId}`);
  return res.data.data;
};

export const createClassApi = async (data: Partial<Class>) => {
  const res = await api.post<{ data: Class }>('/classes', data);
  return res.data.data;
};

export const getSectionsApi = async (classId: string) => {
  const res = await api.get<{ data: Section[] }>(`/classes/${classId}/sections`);
  return res.data.data;
};

export const createSectionApi = async (classId: string, data: Partial<Section>) => {
  const res = await api.post<{ data: Section }>(`/classes/${classId}/sections`, data);
  return res.data.data;
};

export const getSubjectsApi = async () => {
  const res = await api.get<{ data: Subject[] }>('/subjects');
  return res.data.data;
};

export const createSubjectApi = async (data: Partial<Subject>) => {
  const res = await api.post<{ data: Subject }>('/subjects', data);
  return res.data.data;
};

export const assignSubjectsApi = async (classId: string, subjectIds: string[],
                                        teacherMap: Record<string, string>) =>
  api.put(`/classes/${classId}/subjects`, {
    subjectIds,
    teacherAssignments: teacherMap,
  });
```

---

## 9. Frontend: Classes Page (`frontend/src/pages/classes/ClassesPage.tsx`)

Route: `/classes`

### Layout
- **PageHeader**: "Classes & Sections" + "New Class" button
- **Year filter**: uses `selectedYear` from `useAcademicYearStore`
- **Classes Table**: columns: Class Name, Level, Sections Count, Status, Actions
- **Expandable rows**: each class row expands to show its sections inline
  - Section columns: Section Name, Room, Class Teacher, Capacity, Students, Actions
  - "Add Section" button per class row
- **Actions**: Edit Class, Add Section, Delete Class

### Dialogs
- **New/Edit Class**: name input, numeric level, academic year (locked to selected year)
- **New/Edit Section**: name, capacity, room number, assign class teacher (dropdown of teachers)

---

## 10. Frontend: Subjects Page (`frontend/src/pages/classes/SubjectsPage.tsx`)

Route: `/subjects`

- **PageHeader**: "Subjects" + "New Subject" button
- **Subjects Table**: Name, Code, Full Marks, Pass Marks, Elective badge, Status, Actions
- **New/Edit Subject dialog**: all fields
- **Class-Subject Assignment tab**: class selector → show current subjects assigned → multi-select subjects + teacher dropdown per subject → Save

---

## 11. Sidebar Navigation

Add under "Academic" section:
- `Classes & Sections` → `/classes`
- `Subjects` → `/subjects`

---

## Verification Checklist

- [ ] `GET /classes?year_id=X` returns classes for that year only
- [ ] `POST /classes` with duplicate name in same year returns 400
- [ ] Sections are unique per class (same name in different classes allowed)
- [ ] `PUT /classes/{id}/subjects` bulk-assigns subjects; assigns not in list are removed
- [ ] `POST /classes/duplicate` copies all classes+sections to target year without duplicating exams/attendance
- [ ] Class teacher assignment accepts only users with teacher/class_teacher role
- [ ] Frontend Classes page shows expandable section rows
- [ ] Subject assignment matrix shows checkboxes per subject with teacher dropdown
- [ ] Year filter in Classes page responds to navbar year selector
