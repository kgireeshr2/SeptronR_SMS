# PHASE 8 — FEE MANAGEMENT

## Pre-Requisite
Phases 1–7 complete. Students enrolled, academic year set, classes defined.

## Objective
Complete fee management: fee structure, concessions, collection, receipts, due reminders, online payments, defaulter lists, and financial reports.

---

## 8.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 11: Fee Management
fee_categories (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, description TEXT,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, name)
)

fee_structures (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    class_id UUID FK→classes,
    fee_category_id UUID FK→fee_categories,
    amount BIGINT DEFAULT 0,       -- paise
    due_date DATE,
    frequency VARCHAR(20) DEFAULT 'once',  -- once|monthly|quarterly|half_yearly|yearly
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, academic_year_id, class_id, fee_category_id)
)

-- ⚠️ TABLE NAME: fee_discounts (NOT fee_concessions)
fee_discounts (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    discount_type VARCHAR(20) DEFAULT 'percentage',  -- percentage|fixed
    value BIGINT DEFAULT 0,   -- percentage (multiplied by 100) or paise
    applicable_categories JSONB DEFAULT '[]',  -- [fee_category_id, ...]
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at
)

-- ⚠️ TABLE NAME: student_fee_assignments (NOT student_fees)
student_fee_assignments (
    id UUID PK, student_id UUID FK→students ON DELETE CASCADE,
    school_id UUID FK→schools ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    fee_structure_id UUID FK→fee_structures,
    fee_category_id UUID FK→fee_categories,
    original_amount BIGINT,
    discount_id UUID FK→fee_discounts (nullable),   -- NOTE: discount_id not concession_id
    discount_amount BIGINT DEFAULT 0,
    net_amount BIGINT,
    created_at, updated_at,
    UNIQUE(student_id, fee_structure_id)
)

-- ⚠️ FEE INVOICES TABLE (separate from payments — not in original prompt)
fee_invoices (
    id UUID PK, student_id UUID FK→students ON DELETE CASCADE,
    school_id UUID FK→schools ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    invoice_number VARCHAR(50) UNIQUE,
    invoice_date DATE DEFAULT CURRENT_DATE,
    due_date DATE,
    total_amount BIGINT,
    paid_amount BIGINT DEFAULT 0,
    fine_amount BIGINT DEFAULT 0,
    balance_amount BIGINT GENERATED ALWAYS AS (total_amount + fine_amount - paid_amount) STORED,
    invoice_status invoice_status DEFAULT 'unpaid',
        -- ENUM: unpaid|partial|paid|overdue|waived|cancelled
    notes TEXT,
    created_at, updated_at
)

-- ⚠️ TABLE NAME: fee_invoice_items (NOT fee_payment_items)
fee_invoice_items (
    id UUID PK, invoice_id UUID FK→fee_invoices ON DELETE CASCADE,
    assignment_id UUID FK→student_fee_assignments,
    fee_category_id UUID FK→fee_categories,
    amount BIGINT,
    description TEXT,
    created_at
)

fee_payments (
    id UUID PK, student_id UUID FK→students,
    school_id UUID FK→schools ON DELETE CASCADE,
    invoice_id UUID FK→fee_invoices (nullable),
    receipt_number VARCHAR(50) UNIQUE,
    payment_date DATE,
    total_amount BIGINT,
    payment_mode VARCHAR(30),  -- cash|cheque|upi|netbanking|card|online
    bank_name VARCHAR(100), cheque_number VARCHAR(30),
    transaction_id VARCHAR(100), remarks TEXT,
    collected_by UUID FK→users,
    cancelled_at TIMESTAMPTZ, cancelled_by UUID FK→users, cancel_reason TEXT,
    created_at, updated_at
)

-- ⚠️ FINE CONFIGURATIONS TABLE (exists in schema, not in original prompt)
fine_configurations (
    school_id UUID PK FK→schools,
    fine_enabled BOOL DEFAULT FALSE,
    fine_per_day BIGINT DEFAULT 0,   -- paise per day per unpaid fee
    grace_period_days SMALLINT DEFAULT 0,  -- no fine within grace period after due_date
    max_fine_pct SMALLINT DEFAULT 0  -- cap: max fine as % of original amount
)

online_payment_orders (
    id UUID PK, student_id UUID FK→students,
    school_id UUID FK→schools ON DELETE CASCADE,
    order_id VARCHAR(100) UNIQUE,
    gateway VARCHAR(30),        -- razorpay|paytm|ccavenue
    amount BIGINT,
    currency VARCHAR(10) DEFAULT 'INR',
    status VARCHAR(20) DEFAULT 'created',  -- created|attempted|paid|failed|cancelled
    gateway_response JSONB,
    invoice_ids JSONB,       -- NOTE: list of fee_invoice ids (not student_fee ids)
    created_at, updated_at
)
```

> **Architecture note**: The schema uses a 3-layer fee model — **assignment** (what a student owes) → **invoice** (billing document with invoice_number and balance_amount GENERATED column) → **payment** (money collected). A payment links to an invoice. Query pattern: `student_fee_assignments → fee_invoice_items → fee_invoices` to get full fee statement.


---

## 8.2 SQLAlchemy Models (`backend/app/models/fees.py`)

```python
class InvoiceStatus(str, PyEnum):
    # ⚠️ Enum is 'invoice_status' not 'fee_payment_status'
    unpaid = "unpaid"; partial = "partial"; paid = "paid"
    overdue = "overdue"; waived = "waived"; cancelled = "cancelled"

class FeeCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class FeeStructure(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class FeeDiscount(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...    # table: fee_discounts
class StudentFeeAssignment(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...  # table: student_fee_assignments
class FeeInvoice(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...     # table: fee_invoices
class FeeInvoiceItem(Base, UUIDPrimaryKeyMixin): ...                 # table: fee_invoice_items
class FeePayment(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class FineConfiguration(Base): ...                                   # table: fine_configurations (school_id PK)
class OnlinePaymentOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
```

---

## 8.3 Pydantic Schemas

```python
class FeeStructureCreate(BaseModel):
    class_id: UUID
    academic_year_id: UUID
    items: List[FeeStructureItem]

class FeeStructureItem(BaseModel):
    fee_category_id: UUID
    amount: int             # paise
    due_date: Optional[date]
    frequency: str = "once"

class AssignFeesToStudentsRequest(BaseModel):
    academic_year_id: UUID
    class_id: Optional[UUID]   # None = all classes
    discount_map: Optional[Dict[str, UUID]] = {}   # {student_id: discount_id}  # NOTE: discount not concession

class CollectFeeRequest(BaseModel):
    student_id: UUID
    invoice_id: UUID             # ⚠️ payment links to invoice (not directly to student_fee)
    payment_mode: str
    payment_date: date
    bank_name: Optional[str]
    cheque_number: Optional[str]
    transaction_id: Optional[str]
    remarks: Optional[str]

class FeePaymentResponse(BaseModel):
    id: UUID
    receipt_number: str
    student_id: UUID
    student_name: str
    class_section: str
    payment_date: date
    total_amount: int
    payment_mode: str
    fee_items: List[FeePaymentItemDetail]
    collected_by: str
    created_at: datetime

class StudentFeeStatement(BaseModel):
    student_id: UUID
    student_name: str
    academic_year_id: UUID
    fees: List[StudentFeeDetail]
    total_amount: int        # sum net_amount
    total_paid: int          # sum paid_amount
    total_due: int           # sum due_amount
    total_fine: int

class OnlinePaymentInitRequest(BaseModel):
    student_id: UUID
    academic_year_id: UUID
    invoice_ids: List[UUID]    # ⚠️ fee_invoice ids (not student_fee ids)
    gateway: str = "razorpay"

class OnlinePaymentCallbackRequest(BaseModel):
    order_id: str
    gateway_response: dict
```

---

## 8.4 Repository Layer

```python
class FeeRepository:
    async def get_structure(self, school_id: str, year_id: str, class_id: str) -> List[FeeStructure]: ...
    async def upsert_structure(self, school_id: str, class_id: str, year_id: str, items: list) -> List[FeeStructure]: ...
    async def assign_to_students(self, school_id: str, year_id: str, class_id: Optional[str]) -> int: ...
    async def get_student_fee_assignments(self, student_id: str, year_id: str) -> List[StudentFeeAssignment]: ...
    async def get_student_statement(self, student_id: str, year_id: str) -> StudentFeeStatement: ...
    async def apply_concession(self, student_id: str, year_id: str, concession_id: str) -> int: ...
    async def collect_payment(self, school_id: str, data: CollectFeeRequest, collected_by: str) -> FeePayment: ...
    async def get_payment(self, payment_id: str) -> Optional[FeePayment]: ...
    async def cancel_payment(self, payment_id: str, cancelled_by: str, reason: str) -> FeePayment: ...
    async def list_payments(self, school_id: str, filters: dict, page: int, page_size: int) -> tuple: ...
    async def list_defaulters(self, school_id: str, year_id: str, as_of_date: date) -> List[dict]: ...
    async def apply_fine(self, school_id: str, year_id: str, as_of_date: date) -> int: ...
    async def daily_collection_summary(self, school_id: str, date_: date) -> dict: ...
    async def monthly_collection_summary(self, school_id: str, year_id: str, month: int, year: int) -> dict: ...
```

---

## 8.5 Service Layer

```python
async def setup_fee_structure(school_id: str, data: FeeStructureCreate, created_by: str) -> List[FeeStructure]:
    """Upsert fee structure for class + year."""

async def assign_fees_to_students(school_id: str, data: AssignFeesToStudentsRequest, assigned_by: str) -> dict:
    """
    1. Get all enrolled students for class (or all classes if class_id=None)
    2. For each student × fee_structure_item: create StudentFee if not exists
    3. Apply concession from concession_map if provided
    4. Recalculate net_amount, due_amount for each StudentFee
    Returns {assigned: N, skipped: M}
    """

async def collect_fee(school_id: str, data: CollectFeeRequest, collected_by: str) -> FeePayment:
    """
    1. Generate receipt_number (settings: receipt_number_prefix + seq)
    2. Create FeePayment record
    3. Create FeePaymentItem per fee_item
    4. Update StudentFee: paid_amount += item.amount, recalculate due_amount, update status
    5. Enqueue: send_fee_receipt_email + send_fee_receipt_sms
    6. Return FeePayment with receipt
    """

async def cancel_payment(payment_id: str, cancelled_by: str, reason: str) -> FeePayment:
    """
    1. Load payment + items
    2. Reverse each StudentFee: paid_amount -= item.amount, recalculate due/status
    3. Mark payment as cancelled
    4. Log audit
    """

async def run_fine_calculation(school_id: str, year_id: str) -> int:
    """
    1. Load fine settings: fine_enabled, fine_per_day_paise
    2. For overdue unpaid/partial fees: calculate days_overdue × fine_per_day × (due_amount/original)
    3. Update fee_invoice fine_amount, recalculate net_amount, due_amount
    Returns count updated
    """

async def initiate_online_payment(school_id: str, data: OnlinePaymentInitRequest, student_user_id: str) -> dict:
    """
    Create Razorpay order (or other gateway) using gateway API
    Store in online_payment_orders
    Return {order_id, gateway_key, amount, currency}
    """

async def handle_payment_callback(school_id: str, data: OnlinePaymentCallbackRequest) -> FeePayment:
    """
    1. Verify gateway signature
    2. Load order → fee_ids
    3. Call collect_fee() with payment_mode='online', transaction_id from gateway
    4. Update order status
    """
```

---

## 8.6 Receipt Number Generation

```python
# Format from settings: receipt_number_prefix + "-" + YYYY + "-" + zero-padded seq
# Example: RCP-2025-0001
# Use advisory lock or SELECT FOR UPDATE on sequence counter table
```

---

## 8.7 API Endpoints

```
# Fee Categories
GET  /api/v1/fee-categories              → list [fees:view]
POST /api/v1/fee-categories              → create [fees:manage]
PUT  /api/v1/fee-categories/{id}         → update
DELETE /api/v1/fee-categories/{id}       → delete

# Fee Structure
GET  /api/v1/fee-structures              → list by year+class [fees:view]
POST /api/v1/fee-structures              → setup/update structure [fees:manage]
POST /api/v1/fee-structures/assign       → assign to students [fees:manage]

# Fee Discounts (⚠️ endpoints use /fee-discounts not /fee-concessions)
GET  /api/v1/fee-discounts              → list [fees:view]
POST /api/v1/fee-discounts              → create [fees:manage]
PUT  /api/v1/fee-discounts/{id}         → update
DELETE /api/v1/fee-discounts/{id}       → delete
POST /api/v1/fee-discounts/apply        → apply discount to student(s) [fees:manage]

# Fine Configuration
GET  /api/v1/fees/fine-config           → get school fine settings [fees:manage]
PUT  /api/v1/fees/fine-config           → update fine settings [fees:manage]

# Student Fees
GET  /api/v1/fees/student/{student_id}   → fee statement for student [fees:view]
GET  /api/v1/fees/defaulters             → defaulter list (overdue) [fees:report]

# Fee Collection
POST /api/v1/fees/collect                → collect fee → return receipt [fees:collect]
GET  /api/v1/fees/payments               → list payments (filter: date, mode, class) [fees:view]
GET  /api/v1/fees/payments/{id}          → payment detail with items
GET  /api/v1/fees/payments/{id}/receipt  → PDF receipt [fees:view]
POST /api/v1/fees/payments/{id}/cancel   → cancel payment [fees:manage]
GET  /api/v1/fees/export                 → Excel export [fees:export]

# Fine
POST /api/v1/fees/run-fine-calculation   → run fine for overdue [fees:manage]

# Online Payments
POST /api/v1/fees/online/initiate        → initiate gateway order [fees:pay]
POST /api/v1/fees/online/callback        → payment gateway webhook (no auth, verify signature)
GET  /api/v1/fees/online/status/{order_id} → check payment status

# Reports
GET  /api/v1/fees/reports/daily          → daily collection summary [fees:report]
GET  /api/v1/fees/reports/monthly        → monthly summary [fees:report]
GET  /api/v1/fees/reports/class-wise     → fee collection by class [fees:report]
```

---

## 8.8 Fee Receipt PDF Template (`backend/app/templates/fee_receipt.html`)

```html
<!-- WeasyPrint A5 Receipt -->
<div class="receipt">
  <!-- School Header: logo, name, address, phone -->
  <!-- Receipt Title: FEE RECEIPT + receipt_number -->
  <!-- Student Info: name, admission_no, class-section, academic_year -->
  <!-- Payment Table: Fee Type | Amount | Concession | Fine | Net | Paid -->
  <!-- Payment Info: Date, Mode, Transaction ID, Remarks -->
  <!-- Total Row: bold -->
  <!-- Footer: "This is a computer-generated receipt" + school seal -->
  <!-- QR Code linking to receipt verification URL -->
</div>
```

---

## 8.9 Frontend Pages

### `/admin/fees` Page — Main Dashboard
- Stats cards: Total Collected Today, Total Collected This Month, Outstanding Amount, Defaulters Count
- Quick Collect button → opens CollectFee modal

### `/admin/fees/structure` Tab
- Academic Year + Class selectors
- Fee structure table: Category, Amount, Due Date, Frequency
- Edit inline or dialog
- "Assign to Students" button with confirmation (how many students will be assigned)

### `/admin/fees/collect` Modal (accessible from student profile or fees page)
- Student search (admission no, name)
- Shows fee statement: categories, original, concession, fine, net, paid, due
- Checkboxes to select which fees to pay
- Partial payment allowed (input amount per fee)
- Payment mode selector (cash, UPI, cheque, etc.)
- Submit → show receipt preview → Print

### `/admin/fees/receipts` Tab
- Filter: date range, class, section, payment mode, collected by
- Table: Receipt No, Student, Class, Amount, Mode, Date, Collector
- Print receipt per row

### `/admin/fees/defaulters` Tab
- As-of date picker (defaults today)
- Table: Student, Class, Section, Fee Category, Due Date, Days Overdue, Due Amount
- Send reminder bulk action → WhatsApp/SMS all defaulters in selection

### Parent Fees Page (`/parent/fees`)
- Student fee summary for own child
- Download receipts
- Pay Online button → redirect to payment gateway

### `frontend/src/api/fees.ts`
```typescript
export const feesApi = {
  getCategories: () => api.get('/fee-categories'),
  getStructure: (yearId: string, classId: string) =>
    api.get(`/fee-structures?year_id=${yearId}&class_id=${classId}`),
  saveStructure: (data: FeeStructureCreate) => api.post('/fee-structures', data),
  assignToStudents: (data: AssignFeesToStudentsRequest) =>
    api.post('/fee-structures/assign', data),
  getStudentStatement: (studentId: string, yearId: string) =>
    api.get(`/fees/student/${studentId}?year_id=${yearId}`),
  collectFee: (data: CollectFeeRequest) => api.post('/fees/collect', data),
  listPayments: (params: PaymentListParams) => api.get('/fees/payments', { params }),
  getReceipt: (id: string) =>
    api.get(`/fees/payments/${id}/receipt`, { responseType: 'blob' }),
  cancelPayment: (id: string, reason: string) =>
    api.post(`/fees/payments/${id}/cancel`, { reason }),
  getDefaulters: (yearId: string, asOfDate: string) =>
    api.get(`/fees/defaulters?year_id=${yearId}&as_of_date=${asOfDate}`),
  runFineCalc: (yearId: string) =>
    api.post('/fees/run-fine-calculation', { year_id: yearId }),
  initiateOnlinePayment: (data: OnlinePaymentInitRequest) =>
    api.post('/fees/online/initiate', data),
  getDailyReport: (date: string) =>
    api.get(`/fees/reports/daily?date=${date}`),
  getMonthlyReport: (month: number, year: number, yearId: string) =>
    api.get(`/fees/reports/monthly?month=${month}&year=${year}&year_id=${yearId}`),
};
```

---

## 8.10 Celery Tasks

```python
@celery.task(queue="notifications")
def send_fee_receipt_sms(phone: str, student_name: str, amount_paise: int, receipt_number: str): ...

@celery.task(queue="emails")
def send_fee_receipt_email(parent_email: str, student_name: str, receipt_pdf_url: str): ...

@celery.task(queue="notifications")
def send_fee_due_reminder(phone: str, email: str, student_name: str, due_amount: int, due_date: str): ...

# Beat Schedule: daily fine calculation + due reminders
@celery.task(queue="fees")
def daily_fine_calculation():
    """Run for all schools with fine_enabled=true: calculate and apply fines for overdue fees."""

@celery.task(queue="notifications")
def send_due_reminders():
    """For all schools: find fees due in `due_reminder_days_before` days and send reminders."""
```

---

## 8.11 Razorpay Integration (`backend/app/utils/payment_gateway.py`)

```python
import razorpay

class RazorpayGateway:
    def __init__(self, key_id: str, key_secret: str):
        self.client = razorpay.Client(auth=(key_id, key_secret))

    def create_order(self, amount_paise: int, receipt: str, notes: dict) -> dict:
        return self.client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": notes,
        })

    def verify_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        params = f"{order_id}|{payment_id}"
        import hmac, hashlib
        expected = hmac.new(self.key_secret.encode(), params.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
```

---

## 8.12 Tests

```python
async def test_fee_structure_setup(): ...
async def test_assign_fees_to_students(): ...
async def test_collect_fee_partial_payment(): ...   # paid_amount < net_amount → status=partial
async def test_collect_fee_full_payment(): ...      # paid_amount == net_amount → status=paid
async def test_receipt_number_unique_sequential(): ...
async def test_cancel_payment_reverses_balance(): ...
async def test_fine_calculation(): ...              # overdue × fine_per_day
async def test_concession_reduces_net_amount(): ...
async def test_online_payment_signature_verification(): ...  # invalid sig → 400
```

---

## 8.13 Deliverables Checklist

- [ ] Fee category CRUD
- [ ] Fee structure setup per class+year
- [ ] Assign fees to students (bulk) with optional concessions
- [ ] Concession CRUD and application
- [ ] Fee collection with receipt generation (PDF via WeasyPrint)
- [ ] Partial payment supported — status updates (unpaid → partial → paid)
- [ ] Receipt number auto-generated per school settings format
- [ ] Cancel payment with balance reversal
- [ ] Fine calculation engine (daily Celery task)
- [ ] Due reminder Celery task (N days before due_date)
- [ ] Defaulter list with overdue days + amount
- [ ] Online payment gateway (Razorpay) integration
- [ ] Daily and monthly collection summary reports
- [ ] Export fee data to Excel
- [ ] Parent portal: fee statement + receipt download + online pay
