# Feature Prompt 14 — Fee Management

## Round: 3 of 4 — Academic & Financial
## Prerequisites: Prompts 01–09 complete (students enrolled)

---

## Objective

Implement complete school fee management: fee structure definition per class, auto-generation of fee invoices, payment recording, fine on late payment, Razorpay integration hook, receipt PDFs, and financial summaries.

---

## 1. Database Models (`backend/app/models/fee.py`)

```python
import uuid
from datetime import date
from sqlalchemy import String, Boolean, Date, Integer, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
import enum

class FeeFrequency(str, enum.Enum):
    ONE_TIME = "one_time"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"

class PaymentMode(str, enum.Enum):
    CASH = "cash"
    CHEQUE = "cheque"
    ONLINE = "online"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"

class FeeCategory(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "fee_categories"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class FeeStructure(Base, TimestampMixin):
    __tablename__ = "fee_structures"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("classes.id"), nullable=False)
    fee_category_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("fee_categories.id"), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)  # stored in paise
    frequency: Mapped[FeeFrequency] = mapped_column(String(20), default=FeeFrequency.ANNUAL)
    due_day: Mapped[int | None] = mapped_column(Integer, nullable=True)  # day of month
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("academic_year_id", "class_id", "fee_category_id",
                         name="uq_fee_structure"),
    )

class FineConfiguration(Base, TimestampMixin):
    __tablename__ = "fine_configurations"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    fee_category_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("fee_categories.id"), nullable=False)
    fine_type: Mapped[str] = mapped_column(String(20), default="daily")  # daily / fixed
    fine_amount_paise: Mapped[int] = mapped_column(Integer, default=0)
    grace_days: Mapped[int] = mapped_column(Integer, default=5)
    max_fine_paise: Mapped[int] = mapped_column(Integer, default=0)  # 0 = no cap

class FeeInvoice(Base, TimestampMixin):
    __tablename__ = "fee_invoices"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("students.id"), nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    paid_amount_paise: Mapped[int] = mapped_column(Integer, default=0)
    waiver_amount_paise: Mapped[int] = mapped_column(Integer, default=0)
    fine_amount_paise: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="unpaid")  # unpaid/partial/paid
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["FeeInvoiceItem"]] = relationship("FeeInvoiceItem", back_populates="invoice")
    payments: Mapped[list["FeePayment"]] = relationship("FeePayment", back_populates="invoice")

class FeeInvoiceItem(Base, TimestampMixin):
    __tablename__ = "fee_invoice_items"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("fee_invoices.id", ondelete="CASCADE"), nullable=False)
    fee_category_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("fee_categories.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    invoice: Mapped[FeeInvoice] = relationship("FeeInvoice", back_populates="items")

class FeePayment(Base, TimestampMixin):
    __tablename__ = "fee_payments"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("fee_invoices.id"), nullable=False)
    receipt_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_mode: Mapped[PaymentMode] = mapped_column(String(20), nullable=False)
    transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Razorpay order/payment ID
    collected_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    invoice: Mapped[FeeInvoice] = relationship("FeeInvoice", back_populates="payments")
```

---

## 2. Alembic Migration

```sql
CREATE TABLE fee_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE fee_structures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    class_id UUID NOT NULL REFERENCES classes(id),
    fee_category_id UUID NOT NULL REFERENCES fee_categories(id),
    amount_paise INTEGER NOT NULL,
    frequency VARCHAR(20) DEFAULT 'annual' NOT NULL,
    due_day INTEGER,
    is_optional BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_fee_structure UNIQUE (academic_year_id, class_id, fee_category_id)
);

CREATE TABLE fine_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    fee_category_id UUID NOT NULL REFERENCES fee_categories(id),
    fine_type VARCHAR(20) DEFAULT 'daily' NOT NULL,
    fine_amount_paise INTEGER DEFAULT 0 NOT NULL,
    grace_days INTEGER DEFAULT 5 NOT NULL,
    max_fine_paise INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE fee_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id),
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    total_amount_paise INTEGER NOT NULL,
    paid_amount_paise INTEGER DEFAULT 0 NOT NULL,
    waiver_amount_paise INTEGER DEFAULT 0 NOT NULL,
    fine_amount_paise INTEGER DEFAULT 0 NOT NULL,
    status VARCHAR(20) DEFAULT 'unpaid' NOT NULL,
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_fee_invoices_student ON fee_invoices(student_id, academic_year_id);
CREATE INDEX ix_fee_invoices_status ON fee_invoices(school_id, status);

CREATE TABLE fee_invoice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES fee_invoices(id) ON DELETE CASCADE,
    fee_category_id UUID NOT NULL REFERENCES fee_categories(id),
    description VARCHAR(200) NOT NULL,
    amount_paise INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE fee_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES fee_invoices(id),
    receipt_number VARCHAR(50) NOT NULL UNIQUE,
    payment_date DATE NOT NULL,
    amount_paise INTEGER NOT NULL,
    payment_mode VARCHAR(20) NOT NULL,
    transaction_id VARCHAR(100),
    collected_by UUID NOT NULL REFERENCES users(id),
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
```

---

## 3. Pydantic Schemas

```python
class FeeStructureCreate(BaseModel):
    classId: UUID
    feeCategoryId: UUID
    amountPaise: int
    frequency: str = "annual"
    dueDay: int | None = None
    isOptional: bool = False

class GenerateInvoicesRequest(BaseModel):
    academicYearId: UUID
    classIds: list[UUID] | None = None  # None = all classes
    invoiceDate: date
    dueDate: date

class FeePaymentCreate(BaseModel):
    invoiceId: UUID
    amountPaise: int
    paymentMode: str
    paymentDate: date
    transactionId: str | None = None
    remarks: str | None = None

class WaiverRequest(BaseModel):
    invoiceId: UUID
    waiverAmountPaise: int
    reason: str

class FeeInvoiceResponse(BaseModel):
    id: UUID
    invoiceNumber: str
    studentName: str
    admissionNumber: str
    className: str
    invoiceDate: date
    dueDate: date
    totalAmountPaise: int
    paidAmountPaise: int
    waiverAmountPaise: int
    fineAmountPaise: int
    balancePaise: int
    status: str
    items: list[dict]
    model_config = {"from_attributes": True}

class FeeSummary(BaseModel):
    totalInvoiced: int  # paise
    totalCollected: int
    totalOutstanding: int
    totalWaiver: int
    collectionRate: float
    invoiceCount: int
    paidCount: int
    unpaidCount: int
```

---

## 4. Service (`backend/app/services/fee_service.py`)

```python
async def generate_invoices(db, school_id, data: GenerateInvoicesRequest, current_user) -> int:
    """
    For each student enrolled in specified classes:
      1. Get applicable fee structures.
      2. Create FeeInvoice + FeeInvoiceItems.
      3. Generate invoice_number: INV-{YY}-{SEQ:06d} (SELECT FOR UPDATE).
      4. Skip if invoice already exists for same student+year+items.
    Return count of invoices created.
    """

async def record_payment(db, redis, school_id, data: FeePaymentCreate, current_user) -> FeePayment:
    """
    1. Validate invoice exists and belongs to school.
    2. Validate amount <= balance.
    3. Generate receipt_number: RCP-{YY}-{SEQ:06d}.
    4. Create FeePayment.
    5. Update FeeInvoice.paid_amount_paise.
    6. Update status: paid if balance=0, partial otherwise.
    7. Create IncomeRecord in accounting module (via accounting_service.create_fee_income).
    8. Enqueue receipt email/SMS (Celery).
    9. Audit log.
    """

async def apply_waiver(db, school_id, data: WaiverRequest, current_user) -> FeeInvoice:
    """Apply waiver, update status. Only principal/fee_admin can waive."""

async def apply_late_fines(db, redis, school_id, date=None) -> int:
    """
    Called by Celery daily task.
    For each unpaid/partial invoice past due_date (beyond grace_days):
      Calculate fine = days_overdue * fine_per_day (or fixed).
      Update FeeInvoice.fine_amount_paise (capped by max_fine_paise).
    Return count updated.
    """

async def generate_receipt_pdf(db, payment_id, school_id) -> bytes:
    """Render receipt PDF with WeasyPrint."""

async def get_fee_summary(db, school_id, academic_year_id, class_id=None) -> FeeSummary:
    """Aggregate stats for dashboard/reports."""
```

---

## 5. Celery Tasks

```python
@celery_app.task(name="apply_daily_late_fines", queue="scheduled")
def apply_daily_late_fines(school_id: str):
    """Run daily at 00:30 to apply fines to overdue invoices."""

@celery_app.task(name="send_fee_reminder", queue="notifications")
def send_fee_reminder(school_id: str, days_before_due: int = 3):
    """Send SMS/WhatsApp reminders to parents of unpaid invoices."""

@celery_app.task(name="send_payment_receipt", queue="emails")
def send_payment_receipt(payment_id: str, school_id: str):
    """Email receipt PDF to parent."""
```

---

## 6. Razorpay Integration Hook

```python
# backend/app/api/fees.py — Online payment endpoints
POST /fees/online/create-order
    # Creates Razorpay order, returns order_id + key
    # body: { invoice_id, amount_paise }
    # requires RAZORPAY_KEY_ID + RAZORPAY_KEY_SECRET in settings

POST /fees/online/verify
    # Verifies Razorpay signature, calls record_payment with mode=online
    # body: { razorpay_order_id, razorpay_payment_id, razorpay_signature, invoice_id }

POST /fees/online/webhook
    # Razorpay webhook handler (payment.captured event)
    # No auth; verify X-Razorpay-Signature header HMAC-SHA256
```

---

## 7. API Endpoints

```
# Fee Categories
GET    /fee-categories                        → list categories                [fees:view]
POST   /fee-categories                        → create category                [fees:create]
PUT    /fee-categories/{id}                   → update                         [fees:update]

# Fee Structures
GET    /fee-structures?class_id=&year_id=     → list structures                [fees:view]
POST   /fee-structures                        → create structure               [fees:create]
PUT    /fee-structures/{id}                   → update                         [fees:update]
DELETE /fee-structures/{id}                   → delete                         [fees:delete]
POST   /fee-structures/copy-from-year         → copy from previous year        [fees:create]

# Fine Config
GET    /fine-config                            → list fine configs              [fees:view]
POST   /fine-config                            → set fine config                [fees:create]

# Invoices
GET    /fee-invoices?student_id=&status=&year= → list invoices with filters    [fees:view]
POST   /fee-invoices/generate                  → bulk generate invoices        [fees:create]
GET    /fee-invoices/{id}                      → invoice detail                [fees:view]
GET    /fee-invoices/student/{student_id}      → student's invoices           [fees:view]
POST   /fee-invoices/waiver                    → apply waiver                  [fees:update]

# Payments
POST   /fee-payments                           → record payment                [fees:create]
GET    /fee-payments/{id}/receipt              → download receipt PDF          [fees:export]
GET    /fee-payments?date=&mode=               → list payments                 [fees:view]

# Online Payment
POST   /fees/online/create-order               → Razorpay order                [auth]
POST   /fees/online/verify                     → verify payment                [auth]
POST   /fees/online/webhook                    → Razorpay webhook              [public]

# Summary
GET    /fee-summary?year_id=&class_id=         → financial summary             [fees:view]
```

---

## 8. Frontend: Fee Pages

### Fee Structure Setup Page (`/fee-structure`)
- Class vs Fee Category matrix table
- Editable amount cells
- Copy from previous year button
- Frequency and due day configuration

### Fee Invoices Page (`/fee-invoices`)
- Filters: Class, Status (unpaid/partial/paid), Academic Year, Student search
- Table: Student | Class | Invoice# | Amount | Paid | Balance | Status | Due Date | Actions
- Actions: View, Record Payment, Download Receipt, Apply Waiver
- Bulk actions: Send Reminders, Generate Invoices

### Record Payment Modal
- Invoice summary at top
- Amount input (max = balance)
- Payment mode selector
- Transaction ID (shown when online/UPI/bank)
- Print receipt checkbox

### Student Fee Page (within student detail `/students/:id` → Fees tab)
- All invoices for student
- Payment history
- Total dues card

---

## Verification Checklist

- [ ] All amounts stored in paise (×100), displayed in rupees (÷100)
- [ ] Invoice number generated atomically (INV-25-000001)
- [ ] Receipt number generated atomically (RCP-25-000001)
- [ ] Payment updates invoice.paid_amount_paise and status correctly
- [ ] Partial payment leaves status as "partial"
- [ ] Fine calculation respects grace_days and max_fine_paise cap
- [ ] Waiver reduces balance but doesn't change paid_amount
- [ ] Razorpay webhook verifies HMAC-SHA256 signature before processing
- [ ] `record_payment` creates IncomeRecord in accounting module
- [ ] Receipt PDF generated with school letterhead + payment details
- [ ] Reminder Celery task targets invoices 3 days before due_date
