# PHASE 4 — CLASS, SECTION, SUBJECT & TIMETABLE MANAGEMENT

## Pre-Requisite
Phase 3 complete. Academic years exist, school is configured.

## Objective
Full management of classes, sections, subjects, class-subject-teacher assignments, and a visual timetable builder.

---

## 4.1 Database Tables (Verify Exist)

```sql
-- Section 7
classes (
    id UUID PK, school_id UUID FK→schools,
    academic_year_id UUID FK→academic_years,
    name VARCHAR(50),           -- "Grade 1" | "Class 10"
    numeric_level SMALLINT,     -- 1–12 for sorting/promotion
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, academic_year_id, numeric_level)
)

sections (
    id UUID PK, class_id UUID FK→classes ON DELETE CASCADE,
    name VARCHAR(20),           -- "A" | "B" | "Rose"
    capacity SMALLINT DEFAULT 40,
    class_teacher_id UUID FK→users (nullable),
    room_number VARCHAR(20),
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(class_id, name)
)

subjects (
    id UUID PK, school_id UUID FK→schools,
    name VARCHAR(100), code VARCHAR(20),
    is_elective BOOL DEFAULT FALSE,
    full_marks SMALLINT DEFAULT 100,
    pass_marks SMALLINT DEFAULT 35,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, code)
)

class_subjects (
    id UUID PK, class_id UUID FK→classes,
    subject_id UUID FK→subjects, teacher_id UUID FK→users (nullable),
    created_at,
    UNIQUE(class_id, subject_id)
)

timetable (
    id UUID PK, school_id UUID FK→schools,
    section_id UUID FK→sections, subject_id UUID FK→subjects,
    teacher_id UUID FK→users (nullable),
    academic_year_id UUID FK→academic_years,
    day_of_week SMALLINT CHECK(1-7),  -- 1=Mon, 7=Sun
    period_number SMALLINT,
    start_time TIME, end_time TIME,
    created_at, updated_at,
    CHECK(end_time > start_time),
    UNIQUE(section_id, academic_year_id, day_of_week, period_number)
)
```

---

## 4.2 SQLAlchemy Models (`backend/app/models/classes.py`)

```python
class Class(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "classes"
    school_id: UUID, academic_year_id: UUID
    name: str, numeric_level: int, is_active: bool
    # Relationships: sections, enrollments, class_subjects

class Section(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sections"
    class_id: UUID, name: str, capacity: int
    class_teacher_id: Optional[UUID], room_number: Optional[str]
    is_active: bool
    # Relationships: class_, class_teacher, timetable_entries, enrollments

class Subject(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "subjects"
    school_id: UUID, name: str, code: Optional[str]
    is_elective: bool, full_marks: int, pass_marks: int, is_active: bool

class ClassSubject(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "class_subjects"
    class_id: UUID, subject_id: UUID, teacher_id: Optional[UUID]
    # Relationships: class_, subject, teacher

class Timetable(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "timetable"
    school_id: UUID, section_id: UUID, subject_id: UUID
    teacher_id: Optional[UUID], academic_year_id: UUID
    day_of_week: int, period_number: int
    start_time: time, end_time: time
```

---

## 4.3 Pydantic Schemas

```python
class ClassCreate(BaseModel):
    name: str
    numeric_level: int = Field(ge=1, le=12)
    academic_year_id: UUID

class ClassResponse(BaseModel):
    id: UUID
    name: str
    numeric_level: int
    academic_year_id: UUID
    is_active: bool
    sections: Optional[List[SectionResponse]]
    student_count: Optional[int]      # computed at query time
    model_config = ConfigDict(from_attributes=True)

class SectionCreate(BaseModel):
    name: str
    capacity: int = 40
    class_teacher_id: Optional[UUID]
    room_number: Optional[str]

class SectionResponse(BaseModel):
    id: UUID
    class_id: UUID
    name: str
    capacity: int
    class_teacher_id: Optional[UUID]
    class_teacher_name: Optional[str]  # joined
    room_number: Optional[str]
    is_active: bool
    student_count: Optional[int]

class SubjectCreate(BaseModel):
    name: str
    code: Optional[str]
    is_elective: bool = False
    full_marks: int = 100
    pass_marks: int = 35

class SubjectResponse(SubjectCreate):
    id: UUID
    school_id: UUID
    is_active: bool

class ClassSubjectAssign(BaseModel):
    subject_id: UUID
    teacher_id: Optional[UUID]

class ClassSubjectsResponse(BaseModel):
    class_id: UUID
    subjects: List[ClassSubjectDetail]

class ClassSubjectDetail(BaseModel):
    subject_id: UUID
    subject_name: str
    subject_code: Optional[str]
    teacher_id: Optional[UUID]
    teacher_name: Optional[str]

class TimetableEntryCreate(BaseModel):
    subject_id: UUID
    teacher_id: Optional[UUID]
    day_of_week: int = Field(ge=1, le=7)
    period_number: int = Field(ge=1)
    start_time: time
    end_time: time

class TimetableEntryResponse(TimetableEntryCreate):
    id: UUID
    section_id: UUID
    subject_name: str
    teacher_name: Optional[str]

class TimetableGridResponse(BaseModel):
    section_id: UUID
    section_name: str
    class_name: str
    academic_year_id: UUID
    # Grid structure: {day_of_week: {period_number: TimetableEntryResponse}}
    grid: Dict[int, Dict[int, Optional[TimetableEntryResponse]]]
    days: List[str]    # ["Monday", "Tuesday", ...]
    periods: List[int]
```

---

## 4.4 Repository Layer

### `backend/app/repositories/class_repository.py`
```python
class ClassRepository:
    async def list_by_school_year(self, school_id: str, year_id: str) -> List[Class]: ...
    async def get_by_id(self, class_id: str, with_sections: bool = False) -> Optional[Class]: ...
    async def create(self, school_id: str, data: dict) -> Class: ...
    async def update(self, class_id: str, data: dict) -> Class: ...
    async def soft_delete(self, class_id: str, deleted_by: str) -> None: ...
    async def count_students(self, class_id: str, year_id: str) -> int: ...
    async def list_with_student_counts(self, school_id: str, year_id: str) -> List[dict]: ...
```

### `backend/app/repositories/section_repository.py`
```python
class SectionRepository:
    async def list_by_class(self, class_id: str) -> List[Section]: ...
    async def get_by_id(self, section_id: str) -> Optional[Section]: ...
    async def create(self, class_id: str, data: dict) -> Section: ...
    async def update(self, section_id: str, data: dict) -> Section: ...
    async def soft_delete(self, section_id: str) -> None: ...
    async def get_class_teacher_sections(self, teacher_user_id: str, year_id: str) -> List[Section]: ...
```

### `backend/app/repositories/subject_repository.py`
```python
class SubjectRepository:
    async def list_by_school(self, school_id: str, active_only: bool = True) -> List[Subject]: ...
    async def get_by_id(self, subject_id: str) -> Optional[Subject]: ...
    async def create(self, school_id: str, data: dict) -> Subject: ...
    async def update(self, subject_id: str, data: dict) -> Subject: ...
    async def soft_delete(self, subject_id: str) -> None: ...
    async def get_subjects_for_class(self, class_id: str) -> List[ClassSubjectDetail]: ...
    async def assign_to_class(self, class_id: str, subject_id: str, teacher_id: Optional[str]) -> ClassSubject: ...
    async def remove_from_class(self, class_id: str, subject_id: str) -> None: ...
```

### `backend/app/repositories/timetable_repository.py`
```python
class TimetableRepository:
    async def get_grid_for_section(self, section_id: str, year_id: str) -> TimetableGridResponse: ...
    async def get_teacher_schedule(self, teacher_id: str, year_id: str) -> List[TimetableEntryResponse]: ...
    async def upsert_entry(self, section_id: str, year_id: str, school_id: str, data: dict) -> Timetable: ...
    async def delete_entry(self, timetable_id: str) -> None: ...
    async def check_teacher_conflict(self, teacher_id: str, year_id: str, day: int, period: int, exclude_id: Optional[str]) -> bool: ...
    async def check_room_conflict(self, room_number: str, year_id: str, day: int, period: int, exclude_id: Optional[str]) -> bool: ...
    async def bulk_upsert(self, section_id: str, year_id: str, entries: List[dict]) -> int: ...
```

---

## 4.5 Service Layer

### `backend/app/services/class_service.py`
```python
async def create_class(school_id: str, year_id: str, data: ClassCreate) -> Class:
    """Validate numeric_level not duplicate in same year, then create."""

async def duplicate_classes_for_new_year(school_id: str, from_year_id: str, to_year_id: str) -> int:
    """Copy all classes and sections (not timetable) from one year to next with is_active=True."""
```

### `backend/app/services/timetable_service.py`
```python
async def upsert_timetable_entry(section_id: str, year_id: str, school_id: str,
                                  data: TimetableEntryCreate, created_by: str) -> Timetable:
    """
    1. Check teacher conflict: same teacher, same day, same period, same year → 409
    2. Check room conflict if room_number provided on section
    3. Upsert (update if exists for that slot, else create)
    4. Log audit
    """

async def import_timetable_from_csv(section_id: str, year_id: str, school_id: str,
                                     file: UploadFile) -> dict:
    """Parse CSV with columns: day_of_week, period, start_time, end_time, subject_code, teacher_email"""

async def get_timetable_pdf(section_id: str, year_id: str) -> bytes:
    """Generate PDF of section timetable using WeasyPrint."""
```

---

## 4.6 API Endpoints

### Classes
```
GET    /api/v1/classes                         → list classes for school+year [classes:view]
POST   /api/v1/classes                         → create class [classes:create]
GET    /api/v1/classes/{id}                    → get class with sections
PUT    /api/v1/classes/{id}                    → update class [classes:update]
DELETE /api/v1/classes/{id}                    → soft delete [classes:delete]
GET    /api/v1/classes/{id}/sections           → list sections
POST   /api/v1/classes/{id}/sections           → create section [classes:create]
PUT    /api/v1/classes/{id}/sections/{sid}     → update section [classes:update]
DELETE /api/v1/classes/{id}/sections/{sid}     → delete section [classes:delete]
GET    /api/v1/classes/{id}/subjects           → get subject assignments
POST   /api/v1/classes/{id}/subjects           → assign subject to class [classes:manage]
PUT    /api/v1/classes/{id}/subjects/{sub_id}  → update teacher assignment
DELETE /api/v1/classes/{id}/subjects/{sub_id}  → remove subject from class
POST   /api/v1/classes/duplicate-to-year       → copy classes to new year [classes:manage]
POST   /api/v1/classes/bulk-import             → CSV upload [classes:create]
```

### Subjects
```
GET    /api/v1/subjects         → list all subjects for school [subjects:view]
POST   /api/v1/subjects         → create subject [subjects:create]
GET    /api/v1/subjects/{id}    → get subject
PUT    /api/v1/subjects/{id}    → update [subjects:update]
DELETE /api/v1/subjects/{id}    → soft delete [subjects:delete]
```

### Timetable
```
GET  /api/v1/timetable/section/{section_id}   → get grid view for section [timetable:view]
PUT  /api/v1/timetable/section/{section_id}/slot → upsert one slot [timetable:update]
DELETE /api/v1/timetable/{id}                 → delete slot [timetable:delete]
POST /api/v1/timetable/section/{section_id}/bulk → bulk upsert from array
GET  /api/v1/timetable/teacher/{teacher_id}   → teacher's weekly schedule [timetable:view]
GET  /api/v1/timetable/section/{section_id}/export → PDF download [timetable:export]
POST /api/v1/timetable/section/{section_id}/import → CSV import [timetable:create]
```

---

## 4.7 Frontend Pages

### `/admin/classes` Page (Permission: `classes:view`)
**Layout:**
- Page header: "Classes & Sections" + "Add Class" button (permission: `classes:create`)
- Academic year filter (from Zustand store, auto-applied)
- Class cards grid or table: Class Name, Level, Sections Count, Students Count
- Expandable row per class: list of sections with section name, teacher, capacity, enrolled
- Class action buttons: Edit, Add Section, Delete

**Add/Edit Class Dialog:**
- Fields: Class Name (e.g., "Grade 1"), Numeric Level (1-12)
- Academic Year (read-only, from store)

**Add/Edit Section Dialog:**
- Fields: Section Name, Capacity, Class Teacher (searchable dropdown of staff), Room Number

**Subject Assignment Tab:**
- Table view: Subject Name, Subject Code, Assigned Teacher, Elective?
- "Assign Subject" button → dialog with subject picker + teacher picker
- Remove assignment button per row

**Timetable Tab per Section:**
- Visual grid: Y-axis = Days (Mon-Fri or Mon-Sat based on settings), X-axis = Period numbers
- Each cell: Subject + Teacher name
- Click empty cell → add entry dialog (subject, teacher, time)
- Click filled cell → edit/delete
- Print Timetable button → opens PDF in new tab

### `/admin/subjects` Page (Permission: `subjects:view`)
- Simple CRUD table: Subject Name, Code, Full Marks, Pass Marks, Elective, Status
- Add/Edit subject dialog
- "Classes using this subject" count column

### `frontend/src/api/classes.ts`
```typescript
export const classesApi = {
  list: (yearId: string) => api.get(`/classes?year_id=${yearId}`),
  create: (data: ClassCreate) => api.post('/classes', data),
  update: (id: string, data: ClassUpdate) => api.put(`/classes/${id}`, data),
  delete: (id: string) => api.delete(`/classes/${id}`),
  listSections: (classId: string) => api.get(`/classes/${classId}/sections`),
  createSection: (classId: string, data: SectionCreate) => api.post(`/classes/${classId}/sections`, data),
  updateSection: (classId: string, sectionId: string, data: SectionUpdate) =>
    api.put(`/classes/${classId}/sections/${sectionId}`, data),
  getSubjects: (classId: string) => api.get(`/classes/${classId}/subjects`),
  assignSubject: (classId: string, data: ClassSubjectAssign) => api.post(`/classes/${classId}/subjects`, data),
  removeSubject: (classId: string, subjectId: string) => api.delete(`/classes/${classId}/subjects/${subjectId}`),
  duplicateToYear: (fromYearId: string, toYearId: string) =>
    api.post('/classes/duplicate-to-year', { fromYearId, toYearId }),
  bulkImport: (file: File, yearId: string) => {
    const form = new FormData();
    form.append('file', file);
    form.append('year_id', yearId);
    return api.post('/classes/bulk-import', form, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
};

export const timetableApi = {
  getGrid: (sectionId: string, yearId: string) =>
    api.get(`/timetable/section/${sectionId}?year_id=${yearId}`),
  upsertSlot: (sectionId: string, data: TimetableEntryCreate) =>
    api.put(`/timetable/section/${sectionId}/slot`, data),
  deleteSlot: (id: string) => api.delete(`/timetable/${id}`),
  getTeacherSchedule: (teacherId: string, yearId: string) =>
    api.get(`/timetable/teacher/${teacherId}?year_id=${yearId}`),
  exportPdf: (sectionId: string) =>
    api.get(`/timetable/section/${sectionId}/export`, { responseType: 'blob' }),
};
```

---

## 4.8 CSV Bulk Import Formats

### Classes Import CSV
```
class_name,numeric_level,section_names (semicolon-separated)
Grade 1,1,A;B;C
Grade 2,2,A;B
Class 10,10,A;Science;Commerce
```

### Timetable Import CSV
```
day_of_week,period_number,start_time,end_time,subject_code,teacher_email
1,1,08:00,08:45,MATH,john@school.com
1,2,08:45,09:30,ENG,jane@school.com
```

---

## 4.9 Conflict Detection Logic

Teacher conflict: same `teacher_id` + same `academic_year_id` + same `day_of_week` + same `period_number` in ANY section. Must check across all sections, not just current.

Room conflict: same `room_number` (from section) + same `academic_year_id` + same `day_of_week` + same `period_number` in ANY section assigned to same room.

Return 409 Conflict with descriptive message: `"Teacher {name} already has a class at {day} Period {n}: {existing_subject} in {section_name}"`

---

## 4.10 Tests

```python
async def test_create_class_duplicate_level_fails(): ...      # UNIQUE constraint
async def test_section_unique_name_per_class(): ...
async def test_timetable_teacher_conflict_detected(): ...     # → 409
async def test_timetable_room_conflict_detected(): ...        # → 409
async def test_subject_assignment_unique(): ...               # can't assign same sub twice
async def test_duplicate_classes_to_new_year(): ...
async def test_timetable_csv_import(): ...
```

---

## 4.11 Deliverables Checklist

- [ ] Class CRUD with academic year scoping
- [ ] Section CRUD within class — class teacher assignment working
- [ ] Subject CRUD (school-level, not year-specific)
- [ ] Class-subject-teacher assignment working
- [ ] Timetable grid API returns structured day×period dictionary
- [ ] Teacher conflict detection returns 409 with descriptive error
- [ ] Room conflict detection returns 409
- [ ] Timetable PDF export via WeasyPrint
- [ ] Timetable CSV import with validation
- [ ] Frontend classes page with expandable sections
- [ ] Timetable grid UI — interactive cells for add/edit/delete
- [ ] Subject assignment matrix per class in UI
- [ ] Bulk CSV import for classes+sections
- [ ] Teacher schedule view (my timetable for current week)
