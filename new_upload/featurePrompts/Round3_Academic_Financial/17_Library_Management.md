# Feature Prompt 17 — Library Management

## Round: 3 of 4 — Academic & Financial
## Prerequisites: Prompts 09 (Students), 10 (Staff)

---

## Objective

Implement a school library system: book catalog, member management (auto-created for students and staff), book issue/return, fine calculation, reservation/hold queue, and library reports.

---

## 1. Database Models (`backend/app/models/library.py`)

```python
import uuid
from datetime import date
from sqlalchemy import String, Boolean, Date, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
import enum

class Book(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(200), nullable=True)
    edition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(50), default="English")
    total_copies: Mapped[int] = mapped_column(Integer, default=1)
    available_copies: Mapped[int] = mapped_column(Integer, default=1)  # decremented on issue
    rack_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("school_id", "isbn", name="uq_book_isbn"),
    )

class LibraryMember(Base, TimestampMixin):
    __tablename__ = "library_members"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    member_type: Mapped[str] = mapped_column(String(20), nullable=False)  # student / staff
    student_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("students.id"), nullable=True)
    staff_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("staff.id"), nullable=True)
    max_books_allowed: Mapped[int] = mapped_column(Integer, default=3)  # NOTE: max_books_allowed (NOT max_books)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class BookIssue(Base, TimestampMixin):
    __tablename__ = "book_issues"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("books.id"), nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("library_members.id"), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # None = still issued
    fine_per_day_paise: Mapped[int] = mapped_column(Integer, default=200)  # ₹2/day
    fine_amount_paise: Mapped[int] = mapped_column(Integer, default=0)
    fine_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    issued_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)
    returned_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="issued")  # issued / returned / lost

class BookReservation(Base, TimestampMixin):
    __tablename__ = "book_reservations"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("books.id"), nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("library_members.id"), nullable=False)
    reserved_at: Mapped[str] = mapped_column(nullable=False)  # TIMESTAMPTZ
    status: Mapped[str] = mapped_column(String(20), default="waiting")  # waiting / notified / fulfilled / cancelled
```

---

## 2. Alembic Migration

```sql
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    isbn VARCHAR(20),
    title VARCHAR(300) NOT NULL,
    author VARCHAR(200),
    publisher VARCHAR(200),
    edition VARCHAR(50),
    category VARCHAR(100),
    language VARCHAR(50) DEFAULT 'English' NOT NULL,
    total_copies INTEGER DEFAULT 1 NOT NULL,
    available_copies INTEGER DEFAULT 1 NOT NULL,
    rack_location VARCHAR(100),
    cover_image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_book_isbn UNIQUE (school_id, isbn)
);

CREATE INDEX ix_books_school ON books(school_id);
CREATE INDEX ix_books_category ON books(school_id, category);

CREATE TABLE library_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    member_type VARCHAR(20) NOT NULL,
    student_id UUID REFERENCES students(id),
    staff_id UUID REFERENCES staff(id),
    max_books_allowed INTEGER DEFAULT 3 NOT NULL,  -- max_books_allowed (NOT max_books)
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE book_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    book_id UUID NOT NULL REFERENCES books(id),
    member_id UUID NOT NULL REFERENCES library_members(id),
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE,
    fine_per_day_paise INTEGER DEFAULT 200 NOT NULL,
    fine_amount_paise INTEGER DEFAULT 0 NOT NULL,
    fine_paid BOOLEAN DEFAULT FALSE NOT NULL,
    issued_by UUID NOT NULL REFERENCES users(id),
    returned_by UUID,
    status VARCHAR(20) DEFAULT 'issued' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_book_issues_member ON book_issues(member_id, status);
CREATE INDEX ix_book_issues_overdue ON book_issues(school_id, due_date) WHERE status='issued';

CREATE TABLE book_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    book_id UUID NOT NULL REFERENCES books(id),
    member_id UUID NOT NULL REFERENCES library_members(id),
    reserved_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'waiting' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
```

---

## 3. Pydantic Schemas

```python
class BookCreate(BaseModel):
    isbn: str | None = None
    title: str
    author: str | None = None
    publisher: str | None = None
    edition: str | None = None
    category: str | None = None
    language: str = "English"
    totalCopies: int = 1
    rackLocation: str | None = None

class BookIssueCreate(BaseModel):
    bookId: UUID
    memberId: UUID
    dueDate: date
    finePerDayPaise: int = 200

class BookReturnCreate(BaseModel):
    bookIssueId: UUID
    returnDate: date
    fineCollected: bool = False

class BookIssueResponse(BaseModel):
    id: UUID
    bookTitle: str
    memberName: str
    issueDate: date
    dueDate: date
    returnDate: date | None
    daysOverdue: int
    fineAmountPaise: int
    finePaid: bool
    status: str
    model_config = {"from_attributes": True}
```

---

## 4. Service (`backend/app/services/library_service.py`)

```python
async def issue_book(db, school_id, data: BookIssueCreate, current_user) -> BookIssue:
    """
    1. Validate book.available_copies > 0.
    2. Validate member.is_active.
    3. Validate currently_issued_count < member.max_books_allowed.
    4. Validate member has no overdue books.
    5. Create BookIssue; decrement book.available_copies.
    6. If reservations exist for book: skip (reservation will be fulfilled first).
    """

async def return_book(db, issue_id, school_id, data: BookReturnCreate, current_user) -> BookIssue:
    """
    1. Calculate fine = max(0, (return_date - due_date).days) * fine_per_day_paise.
    2. Set return_date, fine_amount_paise, status=returned.
    3. Increment book.available_copies.
    4. If reservations waiting: notify first waiting member.
    5. Audit log.
    """

async def create_member_for_student(db, student_id, school_id) -> LibraryMember:
    """Auto-called when student is created. Creates LibraryMember with max_books_allowed=3."""

async def create_member_for_staff(db, staff_id, school_id) -> LibraryMember:
    """Auto-called when staff is created. Creates LibraryMember with max_books_allowed=5."""

async def get_overdue_books(db, school_id) -> list:
    """All issued books past due_date."""

async def calculate_overdue_fines(db, school_id) -> None:
    """Celery task: daily update of fine_amount_paise for overdue issues."""
```

---

## 5. API Endpoints

```
# Books
GET    /books?category=&q=&available=        → search books                   [library:view]
POST   /books                                → add book                       [library:create]
PUT    /books/{id}                           → update book                    [library:update]
DELETE /books/{id}                           → remove book                    [library:delete]
POST   /books/bulk-import                    → bulk import CSV                [library:create]

# Members
GET    /library-members                      → list members                   [library:view]
GET    /library-members/{id}                 → member detail + issued books   [library:view]

# Issues & Returns
POST   /book-issues                          → issue book                     [library:create]
POST   /book-issues/{id}/return              → return book                    [library:update]
GET    /book-issues?status=&overdue=         → list issues                    [library:view]
GET    /book-issues/overdue                  → overdue issues                 [library:view]

# Reservations
POST   /book-reservations                    → reserve a book                 [library:create]
GET    /book-reservations?book_id=           → view queue                     [library:view]
DELETE /book-reservations/{id}               → cancel reservation             [library:update]

# Reports
GET    /library/report/popular               → most issued books              [library:view]
GET    /library/report/member/{id}           → member issue history           [library:view]
```

---

## 6. Frontend: Library Pages

### Library Page (`/library`)
- **Books tab**: Search books; available copy badge; Issue/Reserve buttons per row
- **Issue Book modal**: Member search → due date → Confirm
- **Return Book modal**: Overdue days + fine amount preview → Confirm
- **Overdue tab**: List of all overdue issues with days overdue + fine

### Book Detail Page
- Book info + cover
- All issue history
- Reservation queue

### Member Library Profile (within Student/Staff detail → Library tab)
- Currently issued books
- Past issues + total fines paid

---

## Verification Checklist

- [ ] `max_books_allowed` field name used (NOT `max_books`)
- [ ] `available_copies` decremented on issue, incremented on return
- [ ] Issue blocked if memberissued_count >= max_books_allowed
- [ ] Issue blocked if member has overdue books
- [ ] Fine calculated correctly: `(return_date - due_date).days * fine_per_day_paise`
- [ ] Reservation queue: first-in first-out, notified on return
- [ ] `create_member_for_student` called from student_service.create_student
- [ ] `create_member_for_staff` called from staff_service.create_staff
- [ ] ISBN uniqueness per school enforced
- [ ] Celery daily task updates fine_amount_paise for all overdue issues
