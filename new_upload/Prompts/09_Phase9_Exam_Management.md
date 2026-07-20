# PHASE 9 — EXAM MANAGEMENT

## Pre-Requisite
Phases 1–8 complete. Students enrolled, subjects assigned to classes, academic year/terms set.

## Objective
Complete exam lifecycle: exam schedule, admit cards, mark entry, grade calculation, report cards (PDF), result publishing with notifications.

---

## 9.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 12: Examinations
exam_types (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,     -- "Unit Test 1" | "Half Yearly" | "Final"
    weightage DECIMAL(5,2) DEFAULT 100.00,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, name)
)

-- ⚠️ CRITICAL: No separate exam_schedules table.
-- The 'exams' table itself has class_id, subject_id, exam_date, full_marks, pass_marks.
-- Each row in exams = one subject exam for one class on one date.
exams (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    term_id UUID FK→academic_terms (nullable),
    exam_type_id UUID FK→exam_types,
    name VARCHAR(200),             -- e.g., "Half Yearly - Mathematics - Class 10"
    class_id UUID FK→classes,      -- ⚠️ direct FK, no exam_schedules table
    subject_id UUID FK→subjects,   -- ⚠️ direct FK, no exam_schedules table
    section_id UUID FK→sections (nullable),
    exam_date DATE,                -- ⚠️ date on exams table itself
    start_time TIME, end_time TIME,
    room_number VARCHAR(20), invigilator_id UUID FK→users (nullable),
    full_marks SMALLINT DEFAULT 100, pass_marks SMALLINT DEFAULT 35,
    status VARCHAR(20) DEFAULT 'scheduled',  -- scheduled|ongoing|completed|results_published
    description TEXT,
    created_by UUID FK→users,
    created_at, updated_at,
    UNIQUE(school_id, academic_year_id, exam_type_id, class_id, subject_id)
)
-- NOTE: To create a "batch exam" (same exam_type, multiple subjects for a class),
-- insert one row per subject. Group them by exam_type_id for display.

-- ⚠️ TABLE NAME: student_marks (NOT exam_marks)
student_marks (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    exam_id UUID FK→exams ON DELETE CASCADE,   -- ⚠️ links to exams.id (not exam_schedule_id)
    student_id UUID FK→students,
    marks_obtained DECIMAL(5,2),
    is_absent BOOL DEFAULT FALSE,
    is_exempted BOOL DEFAULT FALSE,
    grade VARCHAR(5),
    remarks TEXT,
    entered_by UUID FK→users,
    entered_at TIMESTAMPTZ,
    updated_by UUID FK→users, updated_at,
    UNIQUE(exam_id, student_id)
)

-- ⚠️ GRADING SCALE STRUCTURE: One row per school with JSONB (not one row per grade)
grading_scales (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE UNIQUE,
    name VARCHAR(100) DEFAULT 'Default',   -- scale name
    ranges JSONB NOT NULL,  -- array: [{grade, min_pct, max_pct, grade_point, description}]
    -- Example: [{"grade":"A+","min_pct":90,"max_pct":100,"grade_point":4.0,"description":"Outstanding"}]
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at
)
-- NOTE: Access grades via: SELECT range FROM jsonb_array_elements(ranges) AS range
--       WHERE (range->>'min_pct')::numeric <= :pct AND :pct <= (range->>'max_pct')::numeric

-- ⚠️ ADDITIONAL TABLES IN SCHEMA (referenced but missing from original prompt):
report_card_templates (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    template_name VARCHAR(200) NOT NULL,
    exam_type_id UUID FK→exam_types,
    layout_config JSONB,     -- header, footer, columns visibility, signature fields
    is_default BOOL DEFAULT FALSE,
    created_at, updated_at
)

admit_card_configs (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    template_name VARCHAR(200) NOT NULL,
    show_photo BOOL DEFAULT TRUE,
    show_instructions BOOL DEFAULT TRUE,
    instructions TEXT,
    header_note TEXT,
    footer_note TEXT,
    is_default BOOL DEFAULT FALSE,
    created_at, updated_at
)
```

> **Architecture note**: There is **no separate `exam_schedules` table**. Each `exams` row IS the schedule for one class×subject. To show "Exam Schedule for Class 10A - Half Yearly", query `exams WHERE class_id=:cid AND exam_type_id=:tid ORDER BY exam_date`. To enter marks, `POST /exams/{exam_id}/marks` (not `POST /exams/schedules/{id}/marks`).


---

## 9.2 SQLAlchemy Models (`backend/app/models/exams.py`)

```python
class ExamType(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class Exam(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    # ⚠️ Has class_id, subject_id, exam_date directly (no ExamSchedule model)
    ...
class StudentMark(Base, UUIDPrimaryKeyMixin, TimestampMixin):  # table: student_marks
    # exam_id FK→exams (not exam_schedule_id)
    ...
class GradingScale(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    # ranges: Mapped[list] = mapped_column(JSONB)  -- NOT individual rows per grade
    ...
class ReportCardTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class AdmitCardConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
```

---

## 9.3 Pydantic Schemas

```python
class ExamCreate(BaseModel):
    name: str
    academic_year_id: UUID
    term_id: Optional[UUID]
    exam_type_id: UUID
    # ⚠️ class_id, subject_id, dates on the exam itself (no separate schedule create)
    class_id: UUID
    subject_id: UUID
    section_id: Optional[UUID]   # None = all sections
    exam_date: date
    start_time: Optional[time]
    end_time: Optional[time]
    room_number: Optional[str]
    invigilator_id: Optional[UUID]
    full_marks: int = 100
    pass_marks: int = 35
    description: Optional[str]

class ExamBulkCreate(BaseModel):
    """Create multiple exams (one per subject) for same exam_type + class"""
    academic_year_id: UUID
    term_id: Optional[UUID]
    exam_type_id: UUID
    class_id: UUID
    exam_name_prefix: str
    subjects: List[ExamSubjectEntry]

class ExamSubjectEntry(BaseModel):
    subject_id: UUID
    exam_date: date
    start_time: Optional[time]
    end_time: Optional[time]
    full_marks: int = 100
    pass_marks: int = 35

class MarkEntryItem(BaseModel):
    student_id: UUID
    marks_obtained: Optional[float]   # None if absent
    is_absent: bool = False
    is_exempted: bool = False
    remarks: Optional[str]

class MarkEntryRequest(BaseModel):
    # ⚠️ exam_id not exam_schedule_id
    exam_id: UUID
    entries: List[MarkEntryItem]

class ExamMarkResponse(BaseModel):
    student_id: UUID
    student_name: str
    admission_number: str
    roll_number: Optional[str]
    marks_obtained: Optional[float]
    full_marks: int
    pass_marks: int
    grade: Optional[str]
    grade_point: Optional[float]
    percentage: Optional[float]
    is_absent: bool
    is_exempted: bool
    result: str   # "Pass" | "Fail" | "Absent" | "Exempted"

class StudentReportCard(BaseModel):
    student_id: UUID
    student_name: str
    admission_number: str
    class_name: str; section_name: str
    academic_year_name: str
    exam_name: str
    subjects: List[SubjectResult]
    total_marks: float
    total_full_marks: int
    overall_percentage: float
    overall_grade: str
    overall_grade_point: float
    rank: Optional[int]
    attendance_summary: Optional[dict]
    remarks: Optional[str]

class SubjectResult(BaseModel):
    subject_name: str
    full_marks: int; pass_marks: int
    marks_obtained: Optional[float]
    percentage: Optional[float]
    grade: Optional[str]
    grade_point: Optional[float]
    result: str

class GradingScaleUpsert(BaseModel):
    name: str = "Default"
    # ⚠️ Stored as single JSONB array (not per-row entries)
    ranges: List[GradeRange]

class GradeRange(BaseModel):
    grade: str          # e.g., "A+"
    min_pct: float
    max_pct: float
    grade_point: float = 0.0
    description: Optional[str]  # e.g., "Outstanding"

class ResultPublishRequest(BaseModel):
    exam_id: UUID
    notify_parents: bool = True
```

---

## 9.4 Repository Layer

```python
class ExamRepository:
    async def create_exam(self, school_id: str, data: dict) -> Exam: ...
    async def bulk_create_exams(self, school_id: str, exams: list) -> List[Exam]: ...
    async def get_exam(self, exam_id: str) -> Optional[Exam]: ...
    async def list_exams(self, school_id: str, year_id: str, class_id: Optional[str],
                         exam_type_id: Optional[str], status: Optional[str]) -> List[Exam]: ...
    async def update_exam(self, exam_id: str, data: dict) -> Exam: ...
    # ⚠️ No add_schedule — schedules are the exams themselves
    async def bulk_enter_marks(self, exam_id: str, entries: list, entered_by: str) -> int: ...
    async def get_marks_for_exam(self, exam_id: str) -> List[StudentMark]: ...
    async def get_student_marks_for_exam_type(self, student_id: str, exam_type_id: str,
                                               year_id: str) -> List[StudentMark]: ...
    async def get_grading_scale(self, school_id: str) -> Optional[GradingScale]: ...
    async def calculate_grade(self, school_id: str, percentage: float) -> dict: ...
        # Loops over grading_scale.ranges JSONB to find matching grade
    async def publish_results(self, exam_type_id: str, class_id: str, year_id: str) -> int: ...
    async def compute_class_rank(self, exam_type_id: str, class_id: str, year_id: str) -> List[dict]: ...
```

---

## 9.5 Service Layer

```python
async def enter_marks(school_id: str, data: MarkEntryRequest, entered_by: str) -> List[ExamMarkResponse]:
    """
    1. Load schedule + grading scale
    2. For each entry:
       - If is_absent: marks_obtained=None, grade=None
       - Else: calculate percentage, look up grade from grading_scale
    3. Bulk upsert ExamMark records
    4. Return calculated results
    """

async def get_report_card(student_id: str, exam_id: str, school_id: str) -> StudentReportCard:
    """
    1. Load all marks for student in exam
    2. For each subject: compute percentage, grade, grade_point
    3. Compute overall: total_marks / total_full_marks × 100
    4. Get overall_grade from grading scale
    5. Compute class rank (sort all students in section by overall_percentage desc)
    6. Include attendance summary for exam period
    """

async def publish_results(school_id: str, data: ResultPublishRequest) -> dict:
    """
    1. Validate all sections have marks entered
    2. Compute ranks per section
    3. Update exam.status = 'results_published'
    4. If notify_parents:
       Enqueue: send_result_notification_bulk(exam_id, school_id)
    Return {published: True, students_notified: N}
    """

async def generate_report_card_pdf(student_id: str, exam_id: str) -> bytes:
    """Jinja2 + WeasyPrint → report card PDF."""

async def generate_class_marksheet_pdf(exam_id: str, class_id: str) -> bytes:
    """Consolidated marksheet for all students in class."""

async def generate_admit_card(student_id: str, exam_id: str) -> bytes:
    """Admit card with exam schedule, rules, student photo."""
```

---

## 9.6 API Endpoints

```
# Exam Types
GET  /api/v1/exam-types              → list [exams:view]
POST /api/v1/exam-types              → create [exams:manage]
PUT  /api/v1/exam-types/{id}         → update
DELETE /api/v1/exam-types/{id}       → delete

# Grading Scale (⚠️ one scale per school with JSONB ranges)
GET  /api/v1/grading-scales          → get school grading scale [exams:view]
PUT  /api/v1/grading-scales          → upsert entire scale (replace ranges array) [exams:manage]

# Exams (⚠️ no separate /schedules sub-resource)
GET  /api/v1/exams                   → list (filter: year, class, exam_type, status) [exams:view]
POST /api/v1/exams                   → create single exam [exams:create]
POST /api/v1/exams/bulk              → create multiple subject exams for a class [exams:create]
GET  /api/v1/exams/{id}              → get exam detail
PUT  /api/v1/exams/{id}              → update
DELETE /api/v1/exams/{id}            → delete

# Marks (⚠️ exam_id not schedule_id)
GET  /api/v1/exams/{id}/marks        → get mark sheet for exam [marks:view]
POST /api/v1/exams/{id}/marks        → enter/update marks [marks:enter]

# Results & Reports
GET  /api/v1/exams/{id}/report-card/{student_id}   → PDF report card [exams:view]
GET  /api/v1/exams/{id}/admit-card/{student_id}    → PDF admit card [exams:view]
POST /api/v1/exams/{id}/admit-cards/bulk           → bulk admit cards (zip) [exams:export]
GET  /api/v1/exams/{id}/marksheet/{class_id}       → class marksheet PDF [exams:export]
GET  /api/v1/exams/{id}/results/{class_id}         → class results with ranks [exams:view]
POST /api/v1/exams/publish                         → publish results batch [exams:publish]
    body: {exam_type_id, class_id, year_id, notify_parents}

# Report Card & Admit Card Templates
GET  /api/v1/report-card-templates   → list
POST /api/v1/report-card-templates   → create
PUT  /api/v1/report-card-templates/{id} → update
GET  /api/v1/admit-card-configs      → list
POST /api/v1/admit-card-configs      → create
PUT  /api/v1/admit-card-configs/{id} → update
```

---

## 9.7 Frontend Pages

### `/admin/exams` Page (Permission: `exams:view`)
- Tabs: Exams | Exam Types | Grading Scale
- Exams list: Name, Type, Dates, Status, Actions
- Create Exam → dialog: name, type, term, dates
- Exam detail page: schedule table + marks entry

### `/admin/exams/:id` Exam Detail Page
Tabs: Schedule | Mark Entry | Results | Publish

**Schedule Tab:**
- Table: Class, Subject, Date, Time, Room, Invigilator, Full Marks
- Add row button → inline form

**Mark Entry Tab:**
- Select Class → Section → Subject → Load students
- Table: Roll No, Name, Marks input (0–full_marks), Absent checkbox, Grade shown live
- Auto-grade computation as user types marks
- Save Marks button

**Results Tab (after entry):**
- Class topper highlights (rank 1, 2, 3)
- Table: Rank, Name, Subject marks..., Total, %, Grade
- Fail/Pass indicator per row
- Download class marksheet PDF

**Publish Tab:**
- Summary: X/Y students have marks entered
- Notify parents toggle
- Publish Results button (disabled until all marks entered)

### Parent/Student Result View (`/parent/results` or `/student/results`)
- Dropdown: select exam
- View report card for own child
- Download PDF button

### `frontend/src/api/exams.ts`
```typescript
export const examsApi = {
  list: (yearId: string) => api.get(`/exams?year_id=${yearId}`),
  get: (id: string) => api.get(`/exams/${id}`),
  create: (data: ExamCreate) => api.post('/exams', data),
  addSchedule: (examId: string, data: ExamScheduleCreate) =>
    api.post(`/exams/${examId}/schedules`, data),
  getMarks: (scheduleId: string) =>
    api.get(`/exams/schedules/${scheduleId}/marks`),
  enterMarks: (scheduleId: string, data: MarkEntryRequest) =>
    api.post(`/exams/schedules/${scheduleId}/marks`, data),
  getClassResults: (examId: string, classId: string) =>
    api.get(`/exams/${examId}/results/${classId}`),
  publishResults: (examId: string, data: ResultPublishRequest) =>
    api.post(`/exams/${examId}/publish`, data),
  getReportCard: (examId: string, studentId: string) =>
    api.get(`/exams/${examId}/report-card/${studentId}`, { responseType: 'blob' }),
  getAdmitCard: (examId: string, studentId: string) =>
    api.get(`/exams/${examId}/admit-card/${studentId}`, { responseType: 'blob' }),
  getMarksheet: (examId: string, classId: string) =>
    api.get(`/exams/${examId}/marksheet/${classId}`, { responseType: 'blob' }),
};
```

---

## 9.8 Celery Tasks

```python
@celery.task(queue="notifications")
def send_result_notification_bulk(exam_id: str, school_id: str):
    """
    Load all students in exam.
    For each: get primary parent phone.
    If result_sms_on_publish setting is True: send SMS with percentage + grade.
    """

@celery.task(queue="emails")
def send_report_card_email(parent_email: str, student_name: str, report_card_pdf_url: str): ...
```

---

## 9.9 Tests

```python
async def test_mark_entry_auto_grades(): ...        # marks=85 → grade matches scale
async def test_absent_student_no_grade(): ...
async def test_fail_if_below_pass_marks(): ...      # marks < pass_marks → result=Fail
async def test_class_rank_computation(): ...        # correct rank order
async def test_publish_requires_all_marks(): ...    # incomplete → 400
async def test_report_card_pdf_generated(): ...     # returns bytes
async def test_grading_scale_lookup(): ...
async def test_exam_schedule_unique_per_class_subject(): ...
```

---

## 9.10 Deliverables Checklist

- [ ] Exam types and grading scale CRUD
- [ ] Exam creation with subject schedules
- [ ] Admit card PDF generation (Jinja2 + WeasyPrint)
- [ ] Mark entry UI with live grade computation
- [ ] Batch mark entry endpoint (upsert per schedule)
- [ ] Class results with rankings
- [ ] Report card PDF generation per student
- [ ] Class consolidated marksheet PDF
- [ ] Result publishing changes exam status + triggers notifications
- [ ] Parent/student can view and download their report card
- [ ] Failed students report
- [ ] Topper list per class
- [ ] Excel export of exam results
