# PHASE 11 — INVENTORY MANAGEMENT

## Pre-Requisite
Phases 1–10 complete. School configured, staff exist.

## Objective
Track school inventory: item catalog, stock management, purchase orders, issue/return of items, low stock alerts.

---

## 11.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 15: Inventory
inventory_categories (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, description TEXT,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, name)
)

-- ⚠️ ADDITIONAL TABLE: suppliers (in schema, missing from original prompt)
suppliers (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(200),
    phone VARCHAR(20), email VARCHAR(200),
    address TEXT,
    gst_number VARCHAR(20),
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at
)

-- ⚠️ ADDITIONAL TABLE: stores (in schema, missing from original prompt)
stores (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,   -- e.g., "Main Store", "Science Lab", "Library"
    location VARCHAR(200),
    custodian_id UUID FK→staff (nullable),
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at
)

-- ⚠️ TABLE NAME: items (NOT inventory_items)
items (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    store_id UUID FK→stores (nullable),           -- belongs to a store
    category_id UUID FK→inventory_categories,
    name VARCHAR(200) NOT NULL, description TEXT,
    unit VARCHAR(50),          -- pieces|kg|litre|box|ream
    sku VARCHAR(100),
    reorder_level INT DEFAULT 0,
    current_stock INT DEFAULT 0,
    unit_cost BIGINT DEFAULT 0,          -- paise
    is_consumable BOOL DEFAULT TRUE,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, sku)
)

purchase_orders (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    po_number VARCHAR(50),
    supplier_id UUID FK→suppliers,     -- ⚠️ FK to suppliers table (not varchar supplier_name)
    order_date DATE, expected_delivery DATE, actual_delivery DATE,
    status po_status DEFAULT 'draft',
        -- ⚠️ ENUM: draft|sent|partial_received|received|cancelled
        --         (NOT pending|received|partial|cancelled)
    total_amount BIGINT DEFAULT 0,      -- paise
    notes TEXT, approved_by UUID FK→users,
    created_by UUID FK→users, created_at, updated_at,
    UNIQUE(school_id, po_number)
)

purchase_order_items (
    id UUID PK, po_id UUID FK→purchase_orders ON DELETE CASCADE,
    item_id UUID FK→items,             -- ⚠️ FK→items (not inventory_items)
    quantity INT, received_quantity INT DEFAULT 0,
    unit_price BIGINT, total_price BIGINT,
    created_at
)

-- ⚠️ TABLE NAME: stock_entries (NOT inventory_transactions)
stock_entries (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    item_id UUID FK→items ON DELETE CASCADE,      -- ⚠️ FK→items
    entry_type VARCHAR(20),    -- purchase|return|adjustment|damage|write_off
    quantity INT,              -- positive=in, negative=out
    balance_after INT,
    reference_id UUID,
    reference_type VARCHAR(50),  -- purchase_order|stock_issue
    notes TEXT,
    recorded_by UUID FK→users, recorded_at TIMESTAMPTZ,
    created_at
)

-- ⚠️ TABLE NAME: stock_issues (NOT inventory_issues)
stock_issues (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    item_id UUID FK→items ON DELETE CASCADE,       -- ⚠️ FK→items
    issued_to UUID FK→users,
    department VARCHAR(100),
    quantity INT, purpose TEXT,
    issued_by UUID FK→users, issued_at TIMESTAMPTZ,
    returned_quantity INT DEFAULT 0, return_deadline DATE,
    status VARCHAR(20) DEFAULT 'issued',   -- issued|partially_returned|returned
    created_at, updated_at
)
```

---

## 11.2 SQLAlchemy Models (`backend/app/models/inventory.py`)

```python
class POStatus(str, PyEnum):
    draft = "draft"; sent = "sent"; partial_received = "partial_received"
    received = "received"; cancelled = "cancelled"

class InventoryCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class Supplier(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...         # table: suppliers
class Store(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...             # table: stores
class Item(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...              # table: items (NOT inventory_items)
class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class PurchaseOrderItem(Base, UUIDPrimaryKeyMixin): ...
class StockEntry(Base, UUIDPrimaryKeyMixin): ...                        # table: stock_entries
class StockIssue(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...        # table: stock_issues
```

---

## 11.3 Pydantic Schemas

```python
class ItemCreate(BaseModel):    # ⚠️ 'ItemCreate' not 'InventoryItemCreate'
    category_id: UUID
    store_id: Optional[UUID]     # which store this item belongs to
    name: str; description: Optional[str]; unit: str
    sku: Optional[str]
    reorder_level: int = 0
    unit_cost: int = 0   # paise
    is_consumable: bool = True

class PurchaseOrderCreate(BaseModel):
    supplier_id: UUID            # ⚠️ FK to suppliers table (not supplier_name varchar)
    order_date: date; expected_delivery: Optional[date]; notes: Optional[str]
    items: List[POItemCreate]

class POItemCreate(BaseModel):
    item_id: UUID; quantity: int; unit_price: int   # paise
    # item_id FK→items (not inventory_items)

class ReceiveStockRequest(BaseModel):
    po_id: UUID
    items: List[POItemReceive]

class POItemReceive(BaseModel):
    po_item_id: UUID; received_quantity: int; actual_unit_price: Optional[int]

class IssueItemRequest(BaseModel):  # Creates stock_issues record
    item_id: UUID; quantity: int
    issued_to: UUID; department: Optional[str]  # ⚠️ 'department' not 'issued_to_department'
    purpose: str; return_deadline: Optional[date]

class ReturnItemRequest(BaseModel):
    issue_id: UUID; returned_quantity: int

class StockAdjustmentRequest(BaseModel):
    item_id: UUID; quantity: int   # positive or negative
    reason: str   # adjustment|damage|write_off
    notes: Optional[str]
```

---

## 11.4 Service Layer

```python
async def receive_stock(school_id: str, data: ReceiveStockRequest, received_by: str) -> PurchaseOrder:
    """
    For each item in data.items:
    1. Update po_item.received_quantity += received_quantity
    2. Update inventory_item.current_stock += received_quantity
    3. Create InventoryTransaction(type=purchase, quantity=received_quantity)
    4. Update PO status: received/partial based on all items
    Returns updated PO
    """

async def issue_item(school_id: str, data: IssueItemRequest, issued_by: str) -> InventoryIssue:
    """
    1. Check current_stock >= quantity → else 400
    2. Deduct stock: current_stock -= quantity
    3. Create InventoryTransaction(type=issue, quantity=-quantity)
    4. Create InventoryIssue record
    5. Check if new stock <= reorder_level → enqueue low_stock_alert
    """

async def return_item(school_id: str, data: ReturnItemRequest, returned_by: str):
    """Add back to stock, create return transaction, update issue status."""

async def check_low_stock_alerts(school_id: str) -> List[dict]:
    """Items where current_stock <= reorder_level."""
```

---

## 11.5 API Endpoints

```
# Categories
GET  /api/v1/inventory/categories           → list [inventory:view]
POST /api/v1/inventory/categories           → create [inventory:manage]
PUT  /api/v1/inventory/categories/{id}      → update
DELETE /api/v1/inventory/categories/{id}    → delete

# Items
GET  /api/v1/inventory/items                → list (filter: category, low_stock) [inventory:view]
POST /api/v1/inventory/items                → create [inventory:manage]
GET  /api/v1/inventory/items/{id}           → detail with transactions
PUT  /api/v1/inventory/items/{id}           → update
DELETE /api/v1/inventory/items/{id}         → soft delete
POST /api/v1/inventory/items/bulk-import    → CSV import

# Purchase Orders
GET  /api/v1/inventory/purchase-orders      → list [inventory:view]
POST /api/v1/inventory/purchase-orders      → create PO [inventory:purchase]
GET  /api/v1/inventory/purchase-orders/{id} → detail
PUT  /api/v1/inventory/purchase-orders/{id} → update (pending only)
POST /api/v1/inventory/purchase-orders/{id}/receive → receive stock [inventory:purchase]

# Issues
GET  /api/v1/inventory/issues               → list [inventory:view]
POST /api/v1/inventory/issues               → issue item [inventory:issue]
POST /api/v1/inventory/issues/{id}/return   → return item [inventory:issue]

# Adjustments
POST /api/v1/inventory/adjustments          → stock adjustment/damage write-off [inventory:manage]

# Reports
GET  /api/v1/inventory/low-stock            → items at/below reorder level [inventory:view]
GET  /api/v1/inventory/transactions/{item_id} → transaction history for item [inventory:view]
GET  /api/v1/inventory/report               → stock valuation report [inventory:report]
GET  /api/v1/inventory/export               → Excel export [inventory:export]
```

---

## 11.6 Frontend Pages

### `/admin/inventory` Page (Permission: `inventory:view`)

**Dashboard:** Total items, Low stock count, Total stock value, Pending POs

**Items Tab:**
- Table: Name, Category, SKU, Unit, Stock, Reorder Level, Status, Actions
- Low stock items highlighted in amber/red
- Add Item dialog, Edit, Delete

**Purchase Orders Tab:**
- PO list: PO No, Supplier, Date, Items, Total, Status
- Create PO: supplier info + line items with quantity + unit price
- Receive Stock form: per PO item enter received quantity

**Issues & Returns Tab:**
- Issue Item form: item, quantity, issued to (staff), purpose, return deadline
- Active issues table with Return action
- Return dialog: enter quantity returned

**Stock Transactions Tab:**
- Item selector → show full transaction history: date, type, qty, balance, done by

---

## 11.7 Celery Tasks

```python
@celery.task(queue="notifications")
def check_low_stock_alert(school_id: str, item_id: str, current_stock: int, reorder_level: int):
    """Send email to school admin and inventory manager."""
```

---

## 11.8 Tests

```python
async def test_receive_stock_increases_balance(): ...
async def test_issue_deducts_stock(): ...
async def test_issue_insufficient_stock_fails(): ...     # stock < requested qty → 422
async def test_return_restores_stock(): ...
async def test_low_stock_trigger(): ...                  # after issue, stock == reorder_level → alert
async def test_stock_adjustment_negative(): ...          # write-off reduces stock
async def test_transaction_history(): ...
```

---

## 11.9 Deliverables Checklist

- [ ] Item catalog CRUD with categories
- [ ] Purchase order creation and receive stock flow
- [ ] Stock updated on receive with transaction log
- [ ] Issue item with stock deduction and transaction log
- [ ] Return item with stock restoration
- [ ] Stock adjustment (damage/write-off) with reason
- [ ] Low stock alerts triggered on issue + daily Celery check
- [ ] Transaction history per item
- [ ] Stock valuation report (items × unit_cost)
- [ ] Excel export of items and transactions
