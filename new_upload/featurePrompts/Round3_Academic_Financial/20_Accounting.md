# Feature Prompt 20 — Accounting

## Round: 3 of 4 — Academic & Financial
## Prerequisites: Prompts 14 (Fee Management), 15 (Payroll)

---

## Objective

Implement basic school accounting: income records (with automatic fee income sync), expense records, budget heads, bank accounts, and financial reports (P&L, income vs expense summaries).

---

## 1. Database Models (`backend/app/models/accounting.py`)

```python
import uuid
from datetime import date
from sqlalchemy import String, Boolean, Integer, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
import enum

class BudgetHead(Base, TimestampMixin):
    __tablename__ = "budget_heads"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    head_type: Mapped[str] = mapped_column(String(20), nullable=False)  # income / expense
    parent_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("budget_heads.id"), nullable=True)
    budget_amount_paise: Mapped[int] = mapped_column(Integer, default=0)
    academic_year_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class BankAccount(Base, TimestampMixin):
    __tablename__ = "bank_accounts"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    ifsc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    opening_balance_paise: Mapped[int] = mapped_column(Integer, default=0)
    current_balance_paise: Mapped[int] = mapped_column(Integer, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class IncomeRecord(Base, TimestampMixin):
    __tablename__ = "income_records"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    budget_head_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("budget_heads.id"), nullable=True)
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("bank_accounts.id"), nullable=True)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    income_date: Mapped[date] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    payment_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_fee_income: Mapped[bool] = mapped_column(Boolean, default=False)  # True = synced from fee payment
    fee_payment_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    academic_year_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=True)
    recorded_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)


class ExpenseRecord(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "expense_records"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    budget_head_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("budget_heads.id"), nullable=True)
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("bank_accounts.id"), nullable=True)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    expense_date: Mapped[date] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    payment_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vendor_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    academic_year_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=True)
    is_payroll_expense: Mapped[bool] = mapped_column(Boolean, default=False)
    staff_payroll_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    recorded_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

---

## 2. Alembic Migration

```sql
CREATE TABLE budget_heads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    head_type VARCHAR(20) NOT NULL,
    parent_id UUID REFERENCES budget_heads(id),
    budget_amount_paise INTEGER DEFAULT 0 NOT NULL,
    academic_year_id UUID REFERENCES academic_years(id),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    account_name VARCHAR(200) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(50) NOT NULL,
    ifsc_code VARCHAR(20),
    opening_balance_paise INTEGER DEFAULT 0 NOT NULL,
    current_balance_paise INTEGER DEFAULT 0 NOT NULL,
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE income_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    budget_head_id UUID REFERENCES budget_heads(id),
    bank_account_id UUID REFERENCES bank_accounts(id),
    amount_paise INTEGER NOT NULL,
    income_date DATE NOT NULL,
    description VARCHAR(500) NOT NULL,
    payment_mode VARCHAR(20),
    reference_number VARCHAR(100),
    is_fee_income BOOLEAN DEFAULT FALSE NOT NULL,
    fee_payment_id UUID,
    academic_year_id UUID REFERENCES academic_years(id),
    recorded_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_income_records_school_date ON income_records(school_id, income_date);
CREATE INDEX ix_income_records_fee ON income_records(fee_payment_id) WHERE is_fee_income=TRUE;

CREATE TABLE expense_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    budget_head_id UUID REFERENCES budget_heads(id),
    bank_account_id UUID REFERENCES bank_accounts(id),
    amount_paise INTEGER NOT NULL,
    expense_date DATE NOT NULL,
    description VARCHAR(500) NOT NULL,
    payment_mode VARCHAR(20),
    vendor_name VARCHAR(200),
    invoice_number VARCHAR(100),
    receipt_url VARCHAR(500),
    academic_year_id UUID REFERENCES academic_years(id),
    is_payroll_expense BOOLEAN DEFAULT FALSE NOT NULL,
    staff_payroll_id UUID,
    recorded_by UUID NOT NULL REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_expense_records_school_date ON expense_records(school_id, expense_date);
```

---

## 3. Integration Points

### Fee Income Auto-Sync
Called from `fee_service.record_payment()`:
```python
async def create_fee_income(db, payment: FeePayment, current_user):
    """
    Create IncomeRecord(
        is_fee_income=True,
        fee_payment_id=payment.id,
        amount_paise=payment.amount_paise,
        description=f"Fee payment - {student_name} - {invoice_number}",
        payment_mode=payment.payment_mode,
        income_date=payment.payment_date,
    )
    """
```

### Payroll Expense Auto-Sync
Called from `payroll_service.finalize_payroll()`:
```python
async def create_payroll_expense(db, payroll: StaffPayroll, current_user):
    """
    Create ExpenseRecord(
        is_payroll_expense=True,
        staff_payroll_id=payroll.id,
        amount_paise=payroll.net_salary_paise,
        description=f"Salary - {staff_name} - {month}/{year}",
        expense_date=payroll.payment_date,
    )
    """
```

---

## 4. Service (`backend/app/services/accounting_service.py`)

```python
async def create_income(db, school_id, data: IncomeCreate, current_user) -> IncomeRecord:
    """Manual income entry. Update bank_account.current_balance_paise += amount."""

async def create_expense(db, school_id, data: ExpenseCreate, current_user) -> ExpenseRecord:
    """Manual expense entry. Update bank_account.current_balance_paise -= amount."""

async def get_pnl_summary(db, school_id, academic_year_id) -> dict:
    """
    Return:
    {
      total_income_paise, total_expense_paise, net_pnl_paise,
      fee_income_paise, other_income_paise,
      payroll_expense_paise, other_expense_paise,
      income_by_head: [...],
      expense_by_head: [...],
    }
    """

async def get_cashflow(db, school_id, date_from, date_to) -> list:
    """Daily cashflow: grouped by date with income + expense + net."""

async def get_budget_vs_actual(db, school_id, academic_year_id) -> list:
    """Compare budget_amount_paise vs actual spend per expense budget head."""
```

---

## 5. API Endpoints

```
# Budget Heads
GET    /budget-heads?type=income|expense      → list budget heads              [accounting:view]
POST   /budget-heads                          → create budget head            [accounting:create]
PUT    /budget-heads/{id}                     → update                        [accounting:update]

# Bank Accounts
GET    /bank-accounts                         → list accounts                 [accounting:view]
POST   /bank-accounts                         → add account                   [accounting:create]
PUT    /bank-accounts/{id}                    → update account                [accounting:update]

# Income
GET    /income?date_from=&date_to=&type=      → list income records           [accounting:view]
POST   /income                                → manual income entry           [accounting:create]
DELETE /income/{id}                           → delete (soft)                 [accounting:delete]

# Expenses
GET    /expenses?date_from=&date_to=&head=    → list expense records          [accounting:view]
POST   /expenses                              → manual expense                [accounting:create]
POST   /expenses/{id}/receipt                 → upload receipt file           [accounting:update]
DELETE /expenses/{id}                         → delete (soft)                 [accounting:delete]

# Reports
GET    /accounting/pnl?year_id=               → P&L summary                   [accounting:view]
GET    /accounting/cashflow?from=&to=         → daily cashflow                [accounting:view]
GET    /accounting/budget-vs-actual?year_id=  → budget vs actual             [accounting:view]
```

---

## 6. Frontend: Accounting Pages

### Accounting Page (`/accounting`)
- **Income tab**: Date range + budget head filter; income table; + Add Income button
- **Expenses tab**: Expense list with receipt preview; + Add Expense button
- **P&L tab**: Year selector → Income vs Expense donut chart + breakdown table
- **Cash Flow tab**: Bar chart of daily/monthly income vs expense

### Bank Accounts widget
- Balance cards per account
- Opening + total income - total expense = current

---

## Verification Checklist

- [ ] `is_fee_income=True` income records created automatically on fee payment
- [ ] `is_payroll_expense=True` expense records created automatically on payroll finalization
- [ ] `fee_payment_id` uniqueness enforced (one income record per payment)
- [ ] `bank_account.current_balance_paise` updated on every income/expense record
- [ ] P&L summary separates fee income from other income
- [ ] Budget vs Actual compares `budget_heads.budget_amount_paise` to actual totals
- [ ] All amounts stored in paise, displayed in rupees
- [ ] Manual income/expense records support soft delete
- [ ] Expense receipt upload saves file and sets receipt_url
