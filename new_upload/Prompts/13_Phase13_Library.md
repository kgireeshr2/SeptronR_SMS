# PHASE 13 — LIBRARY MANAGEMENT

## Pre-Requisite
Phases 1–12 complete. Students and staff exist.

## Objective
Digital library: book catalog, barcode/accession tracking, issue and return, overdue fine, reservations, and library card generation.

---

## 13.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 18: Library
book_categories (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, is_active BOOL DEFAULT TRUE,
    created_at, updated_at, UNIQUE(school_id, name)
)

books (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    category_id UUID FK→book_categories,
    title VARCHAR(300) NOT NULL, author VARCHAR(200), publisher VARCHAR(200),
    isbn VARCHAR(20), edition VARCHAR(50), publication_year SMALLINT,
    language VARCHAR(50) DEFAULT 'English',
    total_copies SMALLINT DEFAULT 1,
    available_copies SMALLINT DEFAULT 1,   -- managed by trigger/service
    cover_image_url TEXT, description TEXT,
    rack_number VARCHAR(20), is_active BOOL DEFAULT TRUE,
    created_at, updated_at
)
-- ⚠️ NO book_copies table in schema. Books are tracked by count (total_copies/available_copies).
-- If individual copy tracking (barcode per copy) is required, it must be added via Alembic migration.

-- ⚠️ ADDITIONAL TABLE: library_members (not in original prompt)
library_members (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    member_id VARCHAR(20),          -- auto-generated: LIB-001, LIB-002...
    user_id UUID FK→users (nullable),
    member_type VARCHAR(10),        -- student|staff
    entity_id UUID,                 -- student_id or staff_id
    max_books SMALLINT DEFAULT 2,
    membership_valid_until DATE,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, member_id)
)

-- ⚠️ TABLE NAME: book_issues (NOT library_issues)
book_issues (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    book_id UUID FK→books ON DELETE CASCADE,      -- ⚠️ Direct book FK (no book_copy_id)
    member_id UUID FK→library_members,             -- ⚠️ Via library_members table
    issued_by UUID FK→users,
    issue_date DATE NOT NULL, due_date DATE NOT NULL,
    return_date DATE,
    fine_per_day BIGINT,        -- paise (snapshot from settings)
    fine_amount BIGINT DEFAULT 0,
    fine_paid BIGINT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'issued',  -- issued|returned|overdue|lost
    remarks TEXT,
    created_at, updated_at
)
-- NOTE: To issue a book, first ensure borrower has a library_members record.
-- Auto-create library_members if not exists for student/staff.

library_settings (
    school_id UUID PK FK→schools,
    max_books_student SMALLINT DEFAULT 2,
    max_books_staff SMALLINT DEFAULT 5,
    max_loan_days_student SMALLINT DEFAULT 14,
    max_loan_days_staff SMALLINT DEFAULT 30,
    fine_per_day_paise SMALLINT DEFAULT 100,   -- ₹1/day default
    allow_reservations BOOL DEFAULT TRUE
)
```

> **Schema note**: There is **no `book_copies` table** in the schema. Book availability is tracked via `books.available_copies` integer. If per-copy barcode tracking is required, add a `book_copies` table via Alembic migration. The `library_issues` table is named `book_issues` in the actual schema, and it links through `library_members` (not directly to borrower).


---

## 13.2 Pydantic Schemas

```python
class BookCreate(BaseModel):
    category_id: UUID
    title: str; author: Optional[str]; publisher: Optional[str]
    isbn: Optional[str]; edition: Optional[str]; publication_year: Optional[int]
    language: str = "English"
    total_copies: int = 1    # increments available_copies by same amount
    rack_number: Optional[str]; description: Optional[str]

# ⚠️ No AddCopiesRequest (no book_copies table)
# To add more copies: PATCH /library/books/{id} with {total_copies: new_total}

class IssueBookRequest(BaseModel):
    book_id: UUID              # ⚠️ book_id directly (no book_copy_id)
    member_id: Optional[UUID]  # library_members.id — auto-create if not provided
    borrower_type: Literal["student", "staff"]
    borrower_id: UUID          # student_id or staff_id
    due_date: Optional[date]   # or auto from settings: issue_date + max_loan_days

class ReturnBookRequest(BaseModel):
    issue_id: UUID
    condition: str = "good"   # update copy condition
    fine_paid: Optional[int]  # paise collected

class LibraryIssueResponse(BaseModel):
    id: UUID
    book_title: str; book_id: UUID
    member_id: str         # LIB-001 formatted library_members.member_id
    borrower_name: str; borrower_type: str
    issue_date: date; due_date: date; return_date: Optional[date]
    days_overdue: Optional[int]
    fine_amount: int; fine_paid: int; fine_due: int
    status: str
```

---

## 13.3 Service Layer

```python
async def issue_book(school_id: str, data: IssueBookRequest, issued_by: str) -> BookIssue:
    """
    1. Get or create library_members record for borrower
    2. Check member's active issues count <= max_books (from library_settings)
    3. Verify book.available_copies > 0
    4. Decrement book.available_copies
    5. Create BookIssue (book_issues table, status=issued, member_id=member.id)
    6. If any reservations exist for this book → notify next in queue
    """

async def return_book(school_id: str, data: ReturnBookRequest, returned_by: str) -> BookIssue:
    """
    1. Load book_issues record
    2. Calculate overdue_days = max(0, today - due_date)
    3. fine_amount = overdue_days × fine_per_day_paise
    4. Increment book.available_copies
    5. Update book_issues: status=returned, return_date=today, fine_amount, fine_paid
    """

async def calculate_overdue_fines(school_id: str) -> int:
    """Bulk update fine_amount on all overdue issues. Run daily via Celery."""
```

---

## 13.4 API Endpoints

```
# Book Categories
GET/POST/PUT/DELETE /api/v1/library/categories/... [library:manage]

# Books
GET  /api/v1/library/books              → list (filter: category, available_only, search) [library:view]
POST /api/v1/library/books              → create [library:manage]
GET  /api/v1/library/books/{id}         → detail with copies
PUT  /api/v1/library/books/{id}         → update
DELETE /api/v1/library/books/{id}       → delete
POST /api/v1/library/books/{id}/copies  → add copies [library:manage]
GET  /api/v1/library/books/search       → full-text search by title/author/isbn

# Copies
GET  /api/v1/library/copies/{id}        → detail with issue history
PUT  /api/v1/library/copies/{id}        → update condition

# Issues
GET  /api/v1/library/issues             → list (filter: status, overdue) [library:view]
POST /api/v1/library/issues             → issue book [library:issue]
POST /api/v1/library/issues/{id}/return → return book [library:issue]
GET  /api/v1/library/issues/overdue     → overdue list [library:view]
GET  /api/v1/library/issues/borrower/{type}/{id} → issue history for student/staff

# Reservations
GET  /api/v1/library/reservations       → list [library:view]
POST /api/v1/library/reservations       → reserve book [library:view] (any authenticated)
DELETE /api/v1/library/reservations/{id} → cancel

# Reports
GET  /api/v1/library/stats              → counts, top books, most active borrowers
GET  /api/v1/library/export             → Excel export [library:export]
```

---

## 13.5 Frontend Pages

### `/admin/library` Page (Permission: `library:view`)
Tabs: Catalog | Issue/Return | Overdue | Reports

**Catalog Tab:** book cards/table, search, add book, manage copies, cover image
**Issue/Return Tab:** barcode scan field (text input, scan triggers API), or search borrower + select available copy
**Overdue Tab:** list with send-reminder bulk action, collect fine
**Reports:** most borrowed books, top borrowers, monthly issue counts

### Student/Parent Library View (`/student/library`, `/parent/library`)
- My currently issued books + due dates
- Book search (public catalog)
- Reserve book if no copies available

---

## 13.6 Celery Tasks

```python
@celery.task(queue="notifications")
def send_overdue_reminders():
    """Daily: for all schools, find overdue issues, send WhatsApp/SMS to borrower."""

@celery.task(queue="library")
def calculate_all_overdue_fines():
    """Daily: recalculate fine_amount on all issued-and-overdue records."""

@celery.task(queue="notifications")
def notify_reservation_available(reservation_id: str):
    """Send notification when reserved book becomes available."""
```

---

## 13.7 Tests

```python
async def test_issue_book_reduces_available_copies(): ...
async def test_cannot_issue_if_no_copies(): ...
async def test_return_increases_available_copies(): ...
async def test_overdue_fine_calculation(): ...
async def test_max_books_limit_enforced(): ...          # from settings
async def test_reservation_notified_on_return(): ...
```

---

## 13.8 Deliverables Checklist

- [ ] Book catalog CRUD with categories
- [ ] Accession number auto-generation for copies
- [ ] Book copy management (add copies, update condition)
- [ ] Issue book flow (auto-select available copy, check max limit)
- [ ] Return book flow with overdue fine calculation
- [ ] Fine collection recorded in return
- [ ] Reservation system with queue
- [ ] Overdue fine recalculation daily Celery task
- [ ] Overdue notification Celery task
- [ ] Reservation-available notification
- [ ] Library stats (top books, active borrowers)
- [ ] Excel export
- [ ] Student/parent library view with own issues
