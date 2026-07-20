# PHASE 15 — HOMEWORK, LESSON PLANS & PARENT-TEACHER MEETINGS

## Pre-Requisite
Phases 1–14 complete. Classes, sections, subjects, staff, students exist.

## Objective
Homework assignment and submission tracking, digital lesson plan creation, and PTM (Parent-Teacher Meeting) scheduling and feedback.

---

## 15.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 20: Homework & PTM
homework (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    class_id UUID FK→classes, section_id UUID FK→sections (nullable),
    subject_id UUID FK→subjects,
    teacher_id UUID FK→users,
    title VARCHAR(300), description TEXT,
    due_date DATE,
    attachments JSONB DEFAULT '[]',
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at
)

homework_submissions (
    id UUID PK, homework_id UUID FK→homework ON DELETE CASCADE,
    student_id UUID FK→students,
    submitted_at TIMESTAMPTZ,
    content TEXT,
    attachments JSONB DEFAULT '[]',
    -- ⚠️ Schema is simpler: NO status, reviewed_by, reviewed_at, grade, feedback columns
    marks_given DECIMAL(5,2),    -- teacher marks given
    remarks TEXT,                -- teacher remarks
    created_at, updated_at,
    UNIQUE(homework_id, student_id)
)
-- NOTE: If status/reviewed_by/grade fields are needed, add via Alembic migration.

lesson_plans (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    class_id UUID FK→classes, section_id UUID FK→sections (nullable),
    subject_id UUID FK→subjects,
    teacher_id UUID FK→users,
    academic_year_id UUID FK→academic_years,
    title VARCHAR(300),
    plan_date DATE, period_number SMALLINT,
    objectives TEXT, content TEXT,
    resources TEXT,
    -- ⚠️ Schema is simpler: NO teaching_methods, assessment_plan, status, approved_by
    created_at, updated_at,
    UNIQUE(class_id, subject_id, plan_date, period_number)
)
-- NOTE: If approval workflow needed, add 'status' and 'approved_by' via migration.

-- ⚠️ TABLE NAME: ptm_events (NOT ptm_schedules)
ptm_events (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    title VARCHAR(300), description TEXT,
    ptm_date DATE,
    slot_duration_minutes SMALLINT DEFAULT 10,
    venue VARCHAR(200),
    is_active BOOL DEFAULT TRUE,
    created_by UUID FK→users, created_at, updated_at
)

ptm_slots (
    id UUID PK, ptm_event_id UUID FK→ptm_events ON DELETE CASCADE,
    teacher_id UUID FK→users,
    slot_start TIMESTAMPTZ,    -- ⚠️ TIMESTAMPTZ not TIME (field: slot_start not start_time)
    slot_end TIMESTAMPTZ,      -- ⚠️ TIMESTAMPTZ not TIME (field: slot_end not end_time)
    is_booked BOOL DEFAULT FALSE,
    created_at
)

ptm_bookings (
    id UUID PK, slot_id UUID FK→ptm_slots ON DELETE CASCADE,
    student_id UUID FK→students,
    parent_id UUID FK→users,   -- ⚠️ FK→users (not student_parent; parent's user account)
    booked_at TIMESTAMPTZ,
    meeting_notes TEXT,        -- ⚠️ No separate ptm_feedback table; notes inline here
    created_at, updated_at,
    UNIQUE(slot_id)            -- one booking per slot
)
-- NOTE: No separate ptm_feedback table in schema. Meeting notes/feedback stored in ptm_bookings.meeting_notes.
```

---

## 15.2 Pydantic Schemas

```python
class HomeworkCreate(BaseModel):
    class_id: UUID; section_id: Optional[UUID]
    subject_id: UUID; academic_year_id: UUID
    title: str; description: Optional[str]
    due_date: date
    # attachments uploaded via separate file endpoint then IDs passed here

class HomeworkSubmitRequest(BaseModel):
    homework_id: UUID
    content: Optional[str]
    # attachments via file upload

class HomeworkMarkRequest(BaseModel):  # ⚠️ No separate 'review': just update marks_given/remarks
    marks_given: Optional[float]
    remarks: Optional[str]

class LessonPlanCreate(BaseModel):
    class_id: UUID; section_id: Optional[UUID]; subject_id: UUID
    academic_year_id: UUID; plan_date: date; period_number: int
    title: str; objectives: Optional[str]; content: Optional[str]
    resources: Optional[str]
    # ⚠️ No teaching_methods, assessment_plan, status, approved_by in schema
    # Add via migration if approval workflow is required

class PTMEventCreate(BaseModel):   # ⚠️ 'PTMEventCreate' not 'PTMScheduleCreate'
    title: str; description: Optional[str]; academic_year_id: UUID
    ptm_date: date
    slot_duration_minutes: int = 10; venue: Optional[str]

class GenerateSlotsRequest(BaseModel):
    ptm_event_id: UUID              # ⚠️ 'ptm_event_id' not 'ptm_schedule_id'
    teacher_ids: List[UUID]
    start_time: time; end_time: time  # generate slots in this window

class BookPTMSlotRequest(BaseModel):
    slot_id: UUID
    student_id: UUID
    parent_id: UUID   # ⚠️ FK→users (parent's user account ID, not student_parent ID)

class PTMBookingNotesRequest(BaseModel):
    meeting_notes: str    # ⚠️ Stored in ptm_bookings.meeting_notes (no separate ptm_feedback)

class PTMFeedbackCreate(BaseModel):
    ptm_slot_id: UUID; student_id: UUID
    strengths: Optional[str]; improvements: Optional[str]; remarks: Optional[str]
```

---

## 15.3 Service Layer

```python
async def create_homework(school_id: str, data: HomeworkCreate, teacher_id: str) -> Homework:
    """
    1. Create homework record
    2. Enqueue: send_homework_notification (in_app + push) to all students in class/section
    """

async def submit_homework(school_id: str, data: HomeworkSubmitRequest, student_id: str):
    """Create submission, update status=submitted."""

async def review_homework(school_id: str, submission_id: str, data: HomeworkReviewRequest, teacher_id: str):
    """Update submission status, grade, feedback."""

async def generate_ptm_slots(school_id: str, data: GenerateSlotsRequest) -> int:
    """
    For each teacher_id:
    Create time slots from ptm.start_time to ptm.end_time in slot_duration_minutes intervals.
    Returns count of slots created.
    """

async def book_ptm_slot(school_id: str, slot_id: str, student_id: str, parent_id: str) -> PTMSlot:
    """
    1. Check slot is not already booked
    2. Check parent hasn't already booked a slot for this student with this teacher in same PTM
    3. Mark slot as booked
    4. Enqueue: send_ptm_booking_confirmation (SMS to parent)
    """

async def save_ptm_feedback(slot_id: str, data: PTMFeedbackCreate, teacher_id: str) -> PTMFeedback:
    """Save feedback after meeting. Notify parent via in-app/email."""
```

---

## 15.4 API Endpoints

```
# Homework
GET  /api/v1/homework                         → list (filter: class, section, subject, teacher) [homework:view]
POST /api/v1/homework                         → create [homework:create]
GET  /api/v1/homework/{id}                    → detail with submissions
PUT  /api/v1/homework/{id}                    → update [homework:update]
DELETE /api/v1/homework/{id}                  → delete [homework:delete]
POST /api/v1/homework/{id}/attachments        → upload attachment file

GET  /api/v1/homework/{id}/submissions        → list submissions [homework:view]
POST /api/v1/homework/submit                  → student submits [any authenticated]
PUT  /api/v1/homework/submissions/{id}/review → teacher reviews [homework:review]

# Lesson Plans
GET  /api/v1/lesson-plans                     → list (filter: class, subject, teacher, date) [lesson_plans:view]
POST /api/v1/lesson-plans                     → create [lesson_plans:create]
GET  /api/v1/lesson-plans/{id}                → detail
PUT  /api/v1/lesson-plans/{id}                → update [lesson_plans:update]
POST /api/v1/lesson-plans/{id}/submit         → submit for approval
POST /api/v1/lesson-plans/{id}/approve        → approve [lesson_plans:approve]

# PTM
GET  /api/v1/ptm                              → list [ptm:view]
POST /api/v1/ptm                              → create schedule [ptm:manage]
GET  /api/v1/ptm/{id}                         → detail
PUT  /api/v1/ptm/{id}                         → update
POST /api/v1/ptm/{id}/generate-slots          → auto-generate slots [ptm:manage]
GET  /api/v1/ptm/{id}/slots                   → list slots (filter: teacher, booked/available)
POST /api/v1/ptm/book                         → parent books slot
DELETE /api/v1/ptm/slots/{id}/cancel          → cancel booking
POST /api/v1/ptm/slots/{id}/feedback          → teacher saves feedback [ptm:feedback]
GET  /api/v1/ptm/slots/{id}/feedback          → get feedback
GET  /api/v1/ptm/{id}/report                  → PDF report of all meetings [ptm:view]
```

---

## 15.5 Frontend Pages

### `/admin/homework` Page (Permission: `homework:view`)
- Filter: academic year, class, section, subject, teacher
- Table: Title, Class, Subject, Due Date, Submissions Count, Status, Actions
- Create Homework modal: class/section picker, subject, due date, description, file attachments
- Homework detail: list of students + submission status per student

### Teacher Homework View (`/teacher/homework`)
- My assigned homework for current year
- Quick create, view submissions, grade

### Student Homework View (`/student/homework`)
- Pending assignments (due_date >= today)
- Submit button per assignment with file/text upload
- Past assignments with grades/feedback

### `/admin/lesson-plans` Page
- Calendar view: lesson plans by date, color by subject
- Create/edit plan dialog
- Plan approval workflow (if any)

### `/admin/ptm` Page (Permission: `ptm:view`)
- Create PTM Schedule with date/time/venue/slot-duration
- Select teachers → auto-generate slots
- View slot grid per teacher with booked/available status

### Parent PTM Booking View (`/parent/ptm`)
- List available PTMs
- Select teacher → see available slots → book
- My bookings list

### `frontend/src/api/homework.ts` & `frontend/src/api/ptm.ts`
```typescript
export const homeworkApi = {
  list: (params: HomeworkListParams) => api.get('/homework', { params }),
  create: (data: HomeworkCreate) => api.post('/homework', data),
  getDetail: (id: string) => api.get(`/homework/${id}`),
  submit: (data: FormData) => api.post('/homework/submit', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  review: (submissionId: string, data: HomeworkReviewRequest) =>
    api.put(`/homework/submissions/${submissionId}/review`, data),
};

export const ptmApi = {
  list: () => api.get('/ptm'),
  create: (data: PTMScheduleCreate) => api.post('/ptm', data),
  generateSlots: (data: GenerateSlotsRequest) => api.post(`/ptm/${data.ptm_schedule_id}/generate-slots`, data),
  getSlots: (ptmId: string, params: SlotParams) => api.get(`/ptm/${ptmId}/slots`, { params }),
  bookSlot: (data: BookPTMSlotRequest) => api.post('/ptm/book', data),
  cancelBooking: (slotId: string) => api.delete(`/ptm/slots/${slotId}/cancel`),
  saveFeedback: (slotId: string, data: PTMFeedbackCreate) => api.post(`/ptm/slots/${slotId}/feedback`, data),
};
```

---

## 15.6 Celery Tasks

```python
@celery.task(queue="notifications")
def notify_homework_assigned(homework_id: str, school_id: str):
    """Push + in-app notification to all students in target class/section."""

@celery.task(queue="notifications")
def send_homework_due_reminder():
    """Daily: notify students with homework due tomorrow."""

@celery.task(queue="notifications")
def send_ptm_booking_confirmation(parent_phone: str, student_name: str, teacher_name: str, slot_time: str): ...

@celery.task(queue="notifications")
def send_ptm_day_reminder():
    """Day before PTM: send reminder to all booked parents."""
```

---

## 15.7 Tests

```python
async def test_create_homework_notifies_students(): ...
async def test_student_can_submit_once(): ...         # UNIQUE(homework_id, student_id)
async def test_submission_after_due_date_allowed(): ...  # no hard block, just mark
async def test_ptm_slot_double_booking_rejected(): ...
async def test_ptm_parent_one_slot_per_teacher(): ...   # same parent, same teacher, same PTM → 409
async def test_lesson_plan_date_period_unique(): ...
async def test_ptm_feedback_saved_and_notified(): ...
```

---

## 15.8 Deliverables Checklist

- [ ] Homework CRUD with file attachments
- [ ] Homework assignment → push + in-app notifications to students
- [ ] Student homework submission (text + files)
- [ ] Teacher homework review with grade/feedback
- [ ] Homework due reminder Celery task
- [ ] Lesson plan CRUD with approval workflow
- [ ] Lesson plan calendar view
- [ ] PTM schedule creation with slot auto-generation
- [ ] Parent slot booking with conflict prevention
- [ ] PTM booking confirmation SMS
- [ ] PTM day-before reminder
- [ ] Teacher feedback recording after meeting
- [ ] Parent can view PTM feedback for their child
