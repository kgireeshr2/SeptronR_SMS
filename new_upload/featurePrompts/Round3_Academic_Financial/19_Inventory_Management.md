# Feature Prompt 19 — Inventory Management

## Round: 3 of 4 — Academic & Financial
## Prerequisites: Prompts 01–05 complete

---

## Objective

Implement school inventory / store management: item catalog with categories, stock entries (purchase orders), stock issues to departments/staff, low-stock alerts, and full transaction ledger.

> **CRITICAL FIELD NAMES** (from Fix 01):
> - `Item.item_code` (NOT `sku`)
> - `Item.min_stock_level` (NOT `reorder_level`)

---

## 1. Database Models (`backend/app/models/inventory.py`)

```python
import uuid
from sqlalchemy import String, Boolean, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
import enum

class TransactionType(str, enum.Enum):
    PURCHASE = "purchase"
    ISSUE = "issue"
    RETURN = "return"
    ADJUSTMENT = "adjustment"
    OPENING = "opening"

class ItemCategory(Base, TimestampMixin):
    __tablename__ = "item_categories"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Item(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    item_category_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("item_categories.id"), nullable=True)
    item_code: Mapped[str] = mapped_column(String(50), nullable=False)    # NOTE: item_code (NOT sku)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), default="pcs")  # pcs/kg/ltr/box
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    min_stock_level: Mapped[int] = mapped_column(Integer, default=0)      # NOTE: min_stock_level (NOT reorder_level)
    unit_cost_paise: Mapped[int] = mapped_column(Integer, default=0)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("school_id", "item_code", name="uq_item_code"),
    )


class StockEntry(Base, TimestampMixin):
    """Stock purchase/receipt record."""
    __tablename__ = "stock_entries"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cost_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    supplier_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entry_date: Mapped[str] = mapped_column(nullable=False)   # Date
    entered_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


class StockIssue(Base, TimestampMixin):
    """Stock issue to department/staff."""
    __tablename__ = "stock_issues"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    issued_to_department: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("departments.id"), nullable=True)
    issued_to_staff: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("staff.id"), nullable=True)
    issue_date: Mapped[str] = mapped_column(nullable=False)  # Date
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)


class StockTransaction(Base, TimestampMixin):
    """Immutable ledger of all stock movements."""
    __tablename__ = "stock_transactions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("items.id"), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(String(20), nullable=False)
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)  # +ve or -ve
    stock_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    performed_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

---

## 2. Alembic Migration

```sql
CREATE TABLE item_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    item_category_id UUID REFERENCES item_categories(id),
    item_code VARCHAR(50) NOT NULL,       -- item_code (NOT sku)
    name VARCHAR(200) NOT NULL,
    unit VARCHAR(30) DEFAULT 'pcs' NOT NULL,
    current_stock INTEGER DEFAULT 0 NOT NULL,
    min_stock_level INTEGER DEFAULT 0 NOT NULL,  -- min_stock_level (NOT reorder_level)
    unit_cost_paise INTEGER DEFAULT 0 NOT NULL,
    location VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_item_code UNIQUE (school_id, item_code)
);

CREATE INDEX ix_items_school ON items(school_id);
CREATE INDEX ix_items_low_stock ON items(school_id) WHERE current_stock <= min_stock_level;

CREATE TABLE stock_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES items(id),
    quantity INTEGER NOT NULL,
    unit_cost_paise INTEGER NOT NULL,
    total_cost_paise INTEGER NOT NULL,
    supplier_name VARCHAR(200),
    invoice_number VARCHAR(100),
    entry_date DATE NOT NULL,
    entered_by UUID NOT NULL REFERENCES users(id),
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE stock_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES items(id),
    quantity INTEGER NOT NULL,
    issued_to_department UUID REFERENCES departments(id),
    issued_to_staff UUID REFERENCES staff(id),
    issue_date DATE NOT NULL,
    purpose TEXT,
    issued_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE stock_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES items(id),
    transaction_type VARCHAR(20) NOT NULL,
    quantity_change INTEGER NOT NULL,
    stock_after INTEGER NOT NULL,
    reference_id UUID,
    performed_by UUID NOT NULL REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_stock_transactions_item ON stock_transactions(item_id);
```

---

## 3. Service (`backend/app/services/inventory_service.py`)

```python
async def receive_stock(db, school_id, data: StockEntryCreate, current_user) -> StockEntry:
    """
    1. Create StockEntry.
    2. Update Item.current_stock += quantity.
    3. Update Item.unit_cost_paise = latest unit cost.
    4. Create StockTransaction(type=purchase, quantity_change=+quantity).
    5. Audit log.
    """

async def issue_stock(db, school_id, data: StockIssueCreate, current_user) -> StockIssue:
    """
    1. Validate current_stock >= quantity.
    2. Create StockIssue.
    3. Update Item.current_stock -= quantity.
    4. Create StockTransaction(type=issue, quantity_change=-quantity).
    5. Check low stock: if current_stock <= min_stock_level → send alert.
    """

async def adjust_stock(db, school_id, item_id, new_quantity, reason, current_user):
    """Manual adjustment. Creates StockTransaction(type=adjustment)."""

async def get_low_stock_items(db, school_id) -> list[Item]:
    """Items where current_stock <= min_stock_level."""

async def get_item_ledger(db, item_id, school_id) -> list[StockTransaction]:
    """All transactions for an item, ordered by created_at."""
```

---

## 4. API Endpoints

```
# Categories
GET    /item-categories                       → list categories                [inventory:view]
POST   /item-categories                       → create category               [inventory:create]

# Items
GET    /items?category_id=&low_stock=         → list items + low stock filter [inventory:view]
POST   /items                                 → create item                   [inventory:create]
PUT    /items/{id}                            → update item                   [inventory:update]
GET    /items/{id}/ledger                     → item transaction history      [inventory:view]
GET    /items/low-stock                       → items below min_stock_level   [inventory:view]

# Stock Entries (Purchase)
GET    /stock-entries?item_id=&date_from=     → list purchases                [inventory:view]
POST   /stock-entries                         → receive stock                 [inventory:create]

# Stock Issues
GET    /stock-issues?item_id=&dept_id=        → list issues                   [inventory:view]
POST   /stock-issues                          → issue stock                   [inventory:create]

# Adjustments
POST   /stock-adjust                          → manual stock adjustment       [inventory:update]
```

---

## 5. Frontend: Inventory Pages

### Inventory Page (`/inventory`)
- **Items tab**: Table with item_code, name, unit, current stock (red if low), min_stock_level
- **Receive Stock button**: Form for stock entry
- **Issue Stock button**: Form to issue to department/staff
- **Low Stock alert banner**: "X items below minimum stock level"

### Item Detail Page  
- Item info + stock levels
- Transaction ledger table (date, type, quantity change, stock after, performed by)

---

## Verification Checklist

- [ ] `item_code` field name used (NOT `sku`)
- [ ] `min_stock_level` field name used (NOT `reorder_level`)
- [ ] UNIQUE constraint `uq_item_code` on (school_id, item_code)
- [ ] `receive_stock` increments `current_stock` atomically
- [ ] `issue_stock` validates `current_stock >= quantity` before proceeding
- [ ] `StockTransaction` is immutable — never updated after creation
- [ ] Low stock alert fires when `current_stock <= min_stock_level` after issue
- [ ] `stock_after` in StockTransaction reflects actual stock after the operation
- [ ] Item ledger ordered by created_at ascending
