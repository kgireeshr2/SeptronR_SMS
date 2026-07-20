# PHASE 12 — INCOME & EXPENSE ACCOUNTING

## Pre-Requisite
Phases 1–11 complete. Fee payments exist. School configured.

## Objective
Track school income (beyond fees) and expenses, budget management, income/expense categories, vouchers, and financial reporting.

---

## 12.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 16: Accounting (separate income/expense category tables, not unified)

-- ⚠️ SEPARATE TABLES: income_categories and expense_categories (NOT a unified account_categories)
income_categories (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, description TEXT,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, name)
)

expense_categories (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, description TEXT,
    budget_amount BIGINT DEFAULT 0,  -- ⚠️ budget per category built-in (no separate budget table)
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, name)
)

-- ⚠️ TABLE NAME: income_records (NOT income_entries)
income_records (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    category_id UUID FK→income_categories,
    amount BIGINT NOT NULL,             -- paise
    description TEXT,
    income_date DATE NOT NULL,
    payment_mode VARCHAR(30),
    transaction_id VARCHAR(100),
    reference_number VARCHAR(100),
    received_by UUID FK→users,
    is_fee_income BOOL DEFAULT FALSE,   -- true if auto-synced from fee_payments
    fee_payment_id UUID FK→fee_payments (nullable),
    created_by UUID FK→users, created_at, updated_at
)

-- ⚠️ TABLE NAME: expense_records (NOT expense_entries)
expense_records (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    category_id UUID FK→expense_categories,
    amount BIGINT NOT NULL,             -- paise
    description TEXT,
    expense_date DATE NOT NULL,
    payment_mode VARCHAR(30),
    payee_name VARCHAR(200),
    invoice_number VARCHAR(100), invoice_url TEXT,
    approved_by UUID FK→users (nullable),
    status VARCHAR(20) DEFAULT 'approved',   -- draft|pending_approval|approved|rejected
    created_by UUID FK→users, created_at, updated_at
)

-- ⚠️ TABLE NAME: budget_heads (NOT budget_allocations)
-- Note: budget_heads are linked to expense_categories
budget_heads (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    academic_year_id UUID FK→academic_years,
    category_id UUID FK→expense_categories,   -- only expense categories have budgets
    allocated_amount BIGINT NOT NULL,          -- paise
    spent_amount BIGINT DEFAULT 0,
    created_at, updated_at,
    UNIQUE(school_id, academic_year_id, category_id)
)
```

> **Schema note**: There is NO unified `account_categories` table with a `type` field. Use `income_categories` and `expense_categories` as separate tables. Budget is managed via `budget_heads` (expense side only) + `expense_categories.budget_amount` for quick reference.


---

## 12.2 Pydantic Schemas

```python
# ⚠️ Separate category schemas (no unified AccountCategoryCreate)
class IncomeCategoryCreate(BaseModel):
    name: str; description: Optional[str]

class ExpenseCategoryCreate(BaseModel):
    name: str; description: Optional[str]
    budget_amount: int = 0   # paise (store budget on category itself)

class IncomeRecordCreate(BaseModel):   # ⚠️ maps to income_records table
    category_id: UUID                  # FK→income_categories
    academic_year_id: UUID
    amount: int          # paise
    description: str
    income_date: date
    payment_mode: str
    transaction_id: Optional[str]
    reference_number: Optional[str]

class ExpenseRecordCreate(BaseModel):  # ⚠️ maps to expense_records table
    category_id: UUID                  # FK→expense_categories
    academic_year_id: UUID
    amount: int          # paise
    description: str
    expense_date: date
    payment_mode: str
    payee_name: Optional[str]
    invoice_number: Optional[str]

class BudgetHeadCreate(BaseModel):     # ⚠️ maps to budget_heads table
    category_id: UUID                  # FK→expense_categories
    academic_year_id: UUID
    allocated_amount: int   # paise

class FinancialSummaryResponse(BaseModel):
    academic_year_id: UUID
    total_income: int
    total_expense: int
    net_balance: int       # total_income - total_expense
    fee_income: int        # portion from fee_payments
    other_income: int
    income_by_category: List[CategoryAmount]
    expense_by_category: List[CategoryAmount]
    monthly_breakdown: List[MonthlyFinancials]

class CategoryAmount(BaseModel):
    category_name: str
    amount: int
    percentage: float

class MonthlyFinancials(BaseModel):
    month: int; year: int
    income: int; expense: int; balance: int
```

---

## 12.3 Service Layer

```python
async def sync_fee_income(school_id: str, year_id: str) -> int:
    """
    Sync all fee_payments → income_entries (is_fee_income=True).
    Idempotent: skip if fee_payment_id already exists in income_entries.
    """

async def create_expense(school_id: str, data: ExpenseEntryCreate, created_by: str) -> ExpenseEntry:
    """
    1. Create expense entry
    2. Update budget_allocation.spent_amount for category+year
    3. Check if spent > allocated → send over-budget alert
    """

async def get_financial_summary(school_id: str, year_id: str) -> FinancialSummaryResponse:
    """Aggregate income and expense by category and month."""
```

---

## 12.4 API Endpoints

```
# Categories
GET  /api/v1/accounts/categories           → list (filter: type) [accounts:view]
POST /api/v1/accounts/categories           → create [accounts:manage]
PUT  /api/v1/accounts/categories/{id}      → update
DELETE /api/v1/accounts/categories/{id}    → delete

# Income
GET  /api/v1/accounts/income               → list [accounts:view]
POST /api/v1/accounts/income               → create [accounts:create]
GET  /api/v1/accounts/income/{id}          → detail
PUT  /api/v1/accounts/income/{id}          → update [accounts:update]
DELETE /api/v1/accounts/income/{id}        → delete [accounts:delete]
POST /api/v1/accounts/income/sync-fees     → sync fee payments [accounts:manage]

# Expenses
GET  /api/v1/accounts/expenses             → list [accounts:view]
POST /api/v1/accounts/expenses             → create [accounts:create]
GET  /api/v1/accounts/expenses/{id}        → detail
PUT  /api/v1/accounts/expenses/{id}        → update [accounts:update]
DELETE /api/v1/accounts/expenses/{id}      → delete [accounts:delete]
POST /api/v1/accounts/expenses/{id}/approve → approve expense [accounts:approve]

# Budget
GET  /api/v1/accounts/budget               → list allocations [accounts:view]
POST /api/v1/accounts/budget               → set allocation [accounts:manage]
PUT  /api/v1/accounts/budget/{id}          → update allocation

# Reports
GET  /api/v1/accounts/summary              → financial summary [accounts:report]
GET  /api/v1/accounts/profit-loss          → P&L by month/year [accounts:report]
GET  /api/v1/accounts/export               → Excel export [accounts:export]
GET  /api/v1/accounts/income/export        → income Excel
GET  /api/v1/accounts/expenses/export      → expense Excel
```

---

## 12.5 Frontend Pages

### `/admin/accounts` Page (Permission: `accounts:view`)
- Tabs: Dashboard | Income | Expenses | Budget | Reports
- Dashboard: stat cards (Total Income, Total Expense, Net Balance, this month vs last month)
- Monthly bar chart: income vs expense
- Category pie chart: expense breakdown

**Income Tab:** table + add entry dialog + sync-fees button

**Expenses Tab:** table + add entry dialog + upload invoice + approve button (if pending_approval)

**Budget Tab:** category + allocated + spent + remaining; over-budget rows highlighted

**Reports Tab:**
- Date range selector
- P&L statement: income categories, total income, expense categories, total expense, net balance
- Export to Excel / PDF

---

## 12.6 Deliverables Checklist

- [ ] Account categories (income/expense) CRUD
- [ ] Manual income entry CRUD
- [ ] Fee income auto-sync from fee_payments (idempotent)
- [ ] Manual expense entry CRUD with invoice upload
- [ ] Expense approval workflow (optional: draft → pending → approved)
- [ ] Budget allocation per category+year
- [ ] Over-budget alert when expense exceeds allocation
- [ ] Financial summary: income vs expense by category + month
- [ ] P&L report PDF/Excel export
- [ ] Charts on dashboard: monthly bar chart + category pie
