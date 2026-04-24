"""
API Endpoints — Vendor Inventory
Prefix: /vendor-inventory
Allowed roles: superadmin, school_admin, principal, accountant, vendor
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, get_school_id, permission_required
from app.models.auth import User

router = APIRouter(prefix="/vendor-inventory", tags=["Vendor Inventory"])

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _new_id() -> str:
    return str(uuid.uuid4())


def _fmt(paise: int) -> float:
    """Convert paise (integer) → rupees (float) for display."""
    return round(paise / 100, 2)


def _to_paise(rupees: float) -> int:
    return int(round(rupees * 100))


async def _q(db: AsyncSession, sql: str, params: Dict[str, Any] = {}) -> List[Dict]:
    result = await db.execute(text(sql), params)
    rows = result.fetchall()
    return [dict(r._mapping) for r in rows]


async def _scalar(db: AsyncSession, sql: str, params: Dict[str, Any] = {}) -> Any:
    result = await db.execute(text(sql), params)
    row = result.fetchone()
    return row[0] if row else None


def _vendor_filter(user: User) -> tuple[str, Dict]:
    """Return SQL clause + params to filter by vendor if user has vendor role."""
    # We check if the user is linked to a vendor
    return "", {}


# ─── Pydantic schemas ─────────────────────────────────────────────────────────

class VendorCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None


class VendorUpdate(VendorCreate):
    is_active: bool = True


class ProductCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    category: Optional[str] = None
    unit: str = "pcs"
    description: Optional[str] = None
    purchase_price: float = 0   # in rupees
    selling_price: float = 0    # in rupees


class ProductUpdate(ProductCreate):
    is_active: bool = True


class InvoiceItemIn(BaseModel):
    product_id: str
    qty: int
    unit_price: float   # rupees


class InvoiceCreate(BaseModel):
    vendor_id: str
    invoice_number: str
    invoice_date: date
    notes: Optional[str] = None
    items: List[InvoiceItemIn]


class PayInvoiceRequest(BaseModel):
    amount: float   # rupees


class SaleItemIn(BaseModel):
    product_id: str
    qty: int
    unit_price: float   # rupees (can override default selling_price)


class SaleCreate(BaseModel):
    vendor_id: str
    student_id: Optional[str] = None
    sale_date: date
    payment_mode: str = "cash"
    notes: Optional[str] = None
    items: List[SaleItemIn]


class PaymentCreate(BaseModel):
    vendor_id: str
    payment_date: date
    amount: float       # rupees
    direction: str = "to_vendor"
    payment_mode: str = "bank_transfer"
    reference: Optional[str] = None
    notes: Optional[str] = None


# ─── Vendors ──────────────────────────────────────────────────────────────────

@router.get("/vendors")
async def list_vendors(
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(permission_required("vendor_inventory", "view")),
):
    """List all vendors belonging to the current school."""
    if current_user.is_super_admin:
        rows = await _q(db, "SELECT * FROM vendors WHERE is_active=true ORDER BY name")
    else:
        rows = await _q(
            db,
            "SELECT * FROM vendors WHERE school_id = :sid AND is_active=true ORDER BY name",
            {"sid": school_id},
        )
    return {"success": True, "data": rows}


@router.post("/vendors", status_code=status.HTTP_201_CREATED)
async def create_vendor(
    data: VendorCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(permission_required("vendor_inventory", "manage")),
):
    vid = _new_id()
    sid = None if current_user.is_super_admin else school_id
    await db.execute(
        text("""INSERT INTO vendors (id, school_id, name, contact_person, phone, email, address,
                gst_number, bank_name, bank_account, bank_ifsc, is_active, created_at, updated_at)
                VALUES (:id, :sid, :name, :cp, :phone, :email, :addr, :gst, :bank_name, :bank_acct,
                        :bank_ifsc, true, NOW(), NOW())"""),
        {"id": vid, "sid": sid, "name": data.name, "cp": data.contact_person, "phone": data.phone,
         "email": data.email, "addr": data.address, "gst": data.gst_number,
         "bank_name": data.bank_name, "bank_acct": data.bank_account, "bank_ifsc": data.bank_ifsc},
    )
    await db.commit()
    row = (await _q(db, "SELECT * FROM vendors WHERE id = :id", {"id": vid}))[0]
    return {"success": True, "data": row}


@router.put("/vendors/{vendor_id}")
async def update_vendor(
    vendor_id: str,
    data: VendorUpdate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(permission_required("vendor_inventory", "manage")),
):
    school_clause = "" if current_user.is_super_admin else " AND school_id = :sid"
    await db.execute(
        text(f"""UPDATE vendors SET name=:name, contact_person=:cp, phone=:phone, email=:email,
                address=:addr, gst_number=:gst, bank_name=:bank_name, bank_account=:bank_acct,
                bank_ifsc=:bank_ifsc, is_active=:active, updated_at=NOW()
                WHERE id=:id{school_clause}"""),
        {"id": vendor_id, "sid": school_id, "name": data.name, "cp": data.contact_person,
         "phone": data.phone, "email": data.email, "addr": data.address, "gst": data.gst_number,
         "bank_name": data.bank_name, "bank_acct": data.bank_account,
         "bank_ifsc": data.bank_ifsc, "active": 1 if data.is_active else 0},
    )
    await db.commit()
    rows = await _q(db, "SELECT * FROM vendors WHERE id = :id", {"id": vendor_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {"success": True, "data": rows[0]}


# ─── Products ─────────────────────────────────────────────────────────────────

@router.get("/vendors/{vendor_id}/products")
async def list_products(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("vendor_inventory", "view")),
):
    rows = await _q(
        db, "SELECT * FROM vendor_products WHERE vendor_id=:v ORDER BY name",
        {"v": vendor_id},
    )
    # Convert prices to rupees for display
    for r in rows:
        r["purchase_price_rs"] = _fmt(r["purchase_price"])
        r["selling_price_rs"] = _fmt(r["selling_price"])
    return {"success": True, "data": rows}


@router.post("/vendors/{vendor_id}/products", status_code=status.HTTP_201_CREATED)
async def create_product(
    vendor_id: str,
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("vendor_inventory", "manage")),
):
    pid = _new_id()
    await db.execute(
        text("""INSERT INTO vendor_products (id, vendor_id, name, sku, category, unit, description,
                purchase_price, selling_price, is_active, created_at, updated_at)
                VALUES (:id, :v, :name, :sku, :cat, :unit, :desc, :pp, :sp, true, NOW(), NOW())"""),
        {"id": pid, "v": vendor_id, "name": data.name, "sku": data.sku, "cat": data.category,
         "unit": data.unit, "desc": data.description,
         "pp": _to_paise(data.purchase_price), "sp": _to_paise(data.selling_price)},
    )
    await db.commit()
    row = (await _q(db, "SELECT * FROM vendor_products WHERE id=:id", {"id": pid}))[0]
    row["purchase_price_rs"] = _fmt(row["purchase_price"])
    row["selling_price_rs"] = _fmt(row["selling_price"])
    return {"success": True, "data": row}


@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("vendor_inventory", "manage")),
):
    await db.execute(
        text("""UPDATE vendor_products SET name=:name, sku=:sku, category=:cat, unit=:unit,
                description=:desc, purchase_price=:pp, selling_price=:sp, is_active=:active,
                updated_at=NOW() WHERE id=:id"""),
        {"id": product_id, "name": data.name, "sku": data.sku, "cat": data.category,
         "unit": data.unit, "desc": data.description,
         "pp": _to_paise(data.purchase_price), "sp": _to_paise(data.selling_price),
         "active": 1 if data.is_active else 0},
    )
    await db.commit()
    rows = await _q(db, "SELECT * FROM vendor_products WHERE id=:id", {"id": product_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Product not found")
    r = rows[0]
    r["purchase_price_rs"] = _fmt(r["purchase_price"])
    r["selling_price_rs"] = _fmt(r["selling_price"])
    return {"success": True, "data": r}


# ─── Stock ────────────────────────────────────────────────────────────────────

@router.get("/stock")
async def get_stock(
    school_id: str = Depends(get_school_id),
    vendor_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("vendor_inventory", "view")),
):
    vendor_clause = "AND vs.vendor_id = :vid" if vendor_id else ""
    params: Dict[str, Any] = {"sid": school_id}
    if vendor_id:
        params["vid"] = vendor_id

    rows = await _q(
        db,
        f"""SELECT vs.id, vs.vendor_id, vs.product_id, vs.qty_available, vs.qty_reserved,
               vp.name AS product_name, vp.sku, vp.unit, vp.category,
               vp.selling_price,
               v.name AS vendor_name
             FROM vendor_stock vs
             JOIN vendor_products vp ON vp.id = vs.product_id
             JOIN vendors v ON v.id = vs.vendor_id
             WHERE vs.school_id = :sid {vendor_clause}
             ORDER BY v.name, vp.name""",
        params,
    )
    for r in rows:
        r["selling_price_rs"] = _fmt(r["selling_price"])
    return {"success": True, "data": rows}


class AddStockRequest(BaseModel):
    vendor_id: str
    product_id: str
    qty: int = Field(gt=0)


@router.post("/stock")
async def add_stock(
    payload: AddStockRequest,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(permission_required("vendor_inventory", "manage")),
):
    """Directly add / adjust stock quantity for a vendor product."""
    vendor_id = payload.vendor_id
    product_id = payload.product_id
    qty = payload.qty
    # Verify product belongs to this vendor
    prod = await _q(
        db,
        "SELECT id FROM vendor_products WHERE id=:pid AND vendor_id=:vid",
        {"pid": product_id, "vid": vendor_id},
    )
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found for this vendor")
    await _upsert_stock(db, vendor_id, str(school_id), product_id, qty)
    await db.commit()
    return {"success": True, "message": f"Stock updated (+{qty})"}


# ─── Invoices (goods in) ──────────────────────────────────────────────────────

@router.get("/invoices")
async def list_invoices(
    school_id: str = Depends(get_school_id),
    vendor_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("vendor_inventory", "view")),
):
    vendor_clause = "AND vi.vendor_id = :vid" if vendor_id else ""
    params: Dict[str, Any] = {"sid": school_id}
    if vendor_id:
        params["vid"] = vendor_id

    rows = await _q(
        db,
        f"""SELECT vi.*, v.name AS vendor_name
             FROM vendor_invoices vi
             JOIN vendors v ON v.id = vi.vendor_id
             WHERE vi.school_id = :sid {vendor_clause}
             ORDER BY vi.invoice_date DESC""",
        params,
    )
    for r in rows:
        r["total_amount_rs"] = _fmt(r["total_amount"])
        r["paid_amount_rs"] = _fmt(r["paid_amount"])
        r["balance_rs"] = _fmt(r["total_amount"] - r["paid_amount"])
    return {"success": True, "data": rows}


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("vendor_inventory", "manage")),
):
    if not data.items:
        raise HTTPException(status_code=400, detail="Invoice must have at least one item")

    sid = str(school_id)
    inv_date = data.invoice_date.isoformat() if hasattr(data.invoice_date, 'isoformat') else str(data.invoice_date)

    invoice_id = _new_id()
    total_paise = 0
    line_items = []
    for item in data.items:
        item_total = _to_paise(item.unit_price) * item.qty
        total_paise += item_total
        line_items.append({
            "id": _new_id(),
            "invoice_id": invoice_id,
            "product_id": item.product_id,
            "qty": item.qty,
            "unit_price": _to_paise(item.unit_price),
            "total": item_total,
        })

    await db.execute(
        text("""INSERT INTO vendor_invoices (id, vendor_id, school_id, invoice_number, invoice_date,
                total_amount, paid_amount, status, notes, created_at, updated_at)
                VALUES (:id, :vid, :sid, :inv_num, :inv_date, :total, 0, 'unpaid', :notes,
                        NOW(), NOW())"""),
        {"id": invoice_id, "vid": data.vendor_id, "sid": sid,
         "inv_num": data.invoice_number, "inv_date": inv_date,
         "total": total_paise, "notes": data.notes},
    )

    for li in line_items:
        await db.execute(
            text("""INSERT INTO vendor_invoice_items (id, invoice_id, product_id, qty, unit_price, total,
                    created_at, updated_at)
                    VALUES (:id, :invoice_id, :product_id, :qty, :unit_price, :total, NOW(), NOW())"""),
            li,
        )
        # Update stock
        await _upsert_stock(db, data.vendor_id, sid, li["product_id"], li["qty"])

    await db.commit()
    return {"success": True, "data": {"id": invoice_id, "total_amount_rs": _fmt(total_paise)}}


@router.post("/invoices/{invoice_id}/pay")
async def pay_invoice(
    invoice_id: str,
    data: PayInvoiceRequest,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("vendor_inventory", "manage")),
):
    rows = await _q(
        db, "SELECT * FROM vendor_invoices WHERE id=:id AND school_id=:sid",
        {"id": invoice_id, "sid": school_id},
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv = rows[0]
    amount_paise = _to_paise(data.amount)
    new_paid = inv["paid_amount"] + amount_paise
    new_status = "paid" if new_paid >= inv["total_amount"] else "partial"
    await db.execute(
        text("UPDATE vendor_invoices SET paid_amount=:paid, status=:status, updated_at=NOW() WHERE id=:id"),
        {"paid": new_paid, "status": new_status, "id": invoice_id},
    )
    await db.commit()
    return {"success": True, "data": {"paid_amount_rs": _fmt(new_paid), "status": new_status}}


@router.get("/invoices/{invoice_id}/items")
async def get_invoice_items(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("vendor_inventory", "view")),
):
    rows = await _q(
        db,
        """SELECT vii.*, vp.name AS product_name, vp.unit
           FROM vendor_invoice_items vii
           JOIN vendor_products vp ON vp.id = vii.product_id
           WHERE vii.invoice_id = :id""",
        {"id": invoice_id},
    )
    for r in rows:
        r["unit_price_rs"] = _fmt(r["unit_price"])
        r["total_rs"] = _fmt(r["total"])
    return {"success": True, "data": rows}


# ─── Sales ────────────────────────────────────────────────────────────────────

@router.get("/sales")
async def list_sales(
    school_id: str = Depends(get_school_id),
    vendor_id: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("vendor_inventory", "view")),
):
    clauses = ["vs.school_id = :sid"]
    params: Dict[str, Any] = {"sid": school_id}
    if vendor_id:
        clauses.append("vs.vendor_id = :vid")
        params["vid"] = vendor_id
    if from_date:
        clauses.append("vs.sale_date >= :fd")
        params["fd"] = from_date
    if to_date:
        clauses.append("vs.sale_date <= :td")
        params["td"] = to_date

    where = " AND ".join(clauses)
    rows = await _q(
        db,
        f"""SELECT vs.*, v.name AS vendor_name,
               COALESCE(s.first_name + ' ' + s.last_name, 'Walk-in') AS student_name
             FROM vendor_sales vs
             JOIN vendors v ON v.id = vs.vendor_id
             LEFT JOIN students s ON s.id = vs.student_id
             WHERE {where}
             ORDER BY vs.sale_date DESC""",
        params,
    )
    for r in rows:
        r["total_amount_rs"] = _fmt(r["total_amount"])
    return {"success": True, "data": rows}


@router.post("/sales", status_code=status.HTTP_201_CREATED)
async def create_sale(
    data: SaleCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(permission_required("vendor_inventory", "manage")),
):
    if not data.items:
        raise HTTPException(status_code=400, detail="Sale must have at least one item")

    sid = str(school_id)
    sale_date = data.sale_date.isoformat() if hasattr(data.sale_date, 'isoformat') else str(data.sale_date)

    # Validate stock availability
    for item in data.items:
        stock = await _q(
            db,
            "SELECT qty_available FROM vendor_stock WHERE vendor_id=:v AND school_id=:s AND product_id=:p",
            {"v": data.vendor_id, "s": sid, "p": item.product_id},
        )
        available = stock[0]["qty_available"] if stock else 0
        if available < item.qty:
            product = await _q(db, "SELECT name FROM vendor_products WHERE id=:id", {"id": item.product_id})
            pname = product[0]["name"] if product else item.product_id
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{pname}': available={available}, requested={item.qty}",
            )

    sale_id = _new_id()
    total_paise = 0
    line_items = []
    for item in data.items:
        item_total = _to_paise(item.unit_price) * item.qty
        total_paise += item_total
        line_items.append({
            "id": _new_id(),
            "sale_id": sale_id,
            "product_id": item.product_id,
            "qty": item.qty,
            "unit_price": _to_paise(item.unit_price),
            "total": item_total,
        })

    await db.execute(
        text("""INSERT INTO vendor_sales (id, vendor_id, school_id, student_id, sale_date,
                total_amount, payment_mode, received_by, notes, created_at, updated_at)
                VALUES (:id, :vid, :sid, :stud, :sd, :total, :pm, :rb, :notes, NOW(), NOW())"""),
        {"id": sale_id, "vid": data.vendor_id, "sid": sid, "stud": data.student_id,
         "sd": sale_date, "total": total_paise, "pm": data.payment_mode,
         "rb": str(current_user.id), "notes": data.notes},
    )

    for li in line_items:
        await db.execute(
            text("""INSERT INTO vendor_sale_items (id, sale_id, product_id, qty, unit_price, total,
                    created_at, updated_at)
                    VALUES (:id, :sale_id, :product_id, :qty, :unit_price, :total, NOW(), NOW())"""),
            li,
        )
        # Decrement stock
        await db.execute(
            text("UPDATE vendor_stock SET qty_available = qty_available - :qty, updated_at=NOW() "
                 "WHERE vendor_id=:v AND school_id=:s AND product_id=:p"),
            {"qty": li["qty"], "v": data.vendor_id, "s": sid, "p": li["product_id"]},
        )

    await db.commit()
    return {"success": True, "data": {"id": sale_id, "total_amount_rs": _fmt(total_paise)}}


@router.get("/sales/{sale_id}/items")
async def get_sale_items(
    sale_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("vendor_inventory", "view")),
):
    rows = await _q(
        db,
        """SELECT vsi.*, vp.name AS product_name, vp.unit
           FROM vendor_sale_items vsi
           JOIN vendor_products vp ON vp.id = vsi.product_id
           WHERE vsi.sale_id = :id""",
        {"id": sale_id},
    )
    for r in rows:
        r["unit_price_rs"] = _fmt(r["unit_price"])
        r["total_rs"] = _fmt(r["total"])
    return {"success": True, "data": rows}


# ─── Payments ─────────────────────────────────────────────────────────────────

@router.get("/payments")
async def list_payments(
    school_id: str = Depends(get_school_id),
    vendor_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("vendor_inventory", "view")),
):
    vendor_clause = "AND vp.vendor_id = :vid" if vendor_id else ""
    params: Dict[str, Any] = {"sid": school_id}
    if vendor_id:
        params["vid"] = vendor_id

    rows = await _q(
        db,
        f"""SELECT vp.*, v.name AS vendor_name
             FROM vendor_payments vp
             JOIN vendors v ON v.id = vp.vendor_id
             WHERE vp.school_id = :sid {vendor_clause}
             ORDER BY vp.payment_date DESC""",
        params,
    )
    for r in rows:
        r["amount_rs"] = _fmt(r["amount"])
    return {"success": True, "data": rows}


@router.post("/payments", status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _=Depends(permission_required("vendor_inventory", "manage")),
):
    sid = str(school_id)
    pay_date = data.payment_date.isoformat() if hasattr(data.payment_date, 'isoformat') else str(data.payment_date)
    pid = _new_id()
    await db.execute(
        text("""INSERT INTO vendor_payments (id, vendor_id, school_id, payment_date, amount,
                direction, payment_mode, reference, notes, recorded_by, created_at, updated_at)
                VALUES (:id, :vid, :sid, :pd, :amount, :dir, :pm, :ref, :notes, :rb,
                        NOW(), NOW())"""),
        {"id": pid, "vid": data.vendor_id, "sid": sid, "pd": pay_date,
         "amount": _to_paise(data.amount), "dir": data.direction, "pm": data.payment_mode,
         "ref": data.reference, "notes": data.notes, "rb": str(current_user.id)},
    )
    await db.commit()
    return {"success": True, "data": {"id": pid}}


# ─── Balance Sheet ────────────────────────────────────────────────────────────

@router.get("/balance-sheet")
async def balance_sheet(
    vendor_id: str = Query(...),
    school_id: str = Depends(get_school_id),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("vendor_inventory", "view")),
):
    date_clause_inv = ""
    date_clause_sale = ""
    date_clause_pay = ""
    params: Dict[str, Any] = {"vid": vendor_id, "sid": school_id}

    if from_date:
        date_clause_inv += " AND invoice_date >= :fd"
        date_clause_sale += " AND sale_date >= :fd"
        date_clause_pay += " AND payment_date >= :fd"
        params["fd"] = from_date
    if to_date:
        date_clause_inv += " AND invoice_date <= :td"
        date_clause_sale += " AND sale_date <= :td"
        date_clause_pay += " AND payment_date <= :td"
        params["td"] = to_date

    total_purchases = await _scalar(
        db,
        f"SELECT COALESCE(SUM(total_amount),0) FROM vendor_invoices "
        f"WHERE vendor_id=:vid AND school_id=:sid {date_clause_inv}",
        params,
    ) or 0

    total_paid_to_vendor = await _scalar(
        db,
        f"SELECT COALESCE(SUM(amount),0) FROM vendor_payments "
        f"WHERE vendor_id=:vid AND school_id=:sid AND direction='to_vendor' {date_clause_pay}",
        params,
    ) or 0

    total_sales_revenue = await _scalar(
        db,
        f"SELECT COALESCE(SUM(total_amount),0) FROM vendor_sales "
        f"WHERE vendor_id=:vid AND school_id=:sid {date_clause_sale}",
        params,
    ) or 0

    # Purchase cost of items sold (based on purchase_price at time of invoice)
    cogs = await _scalar(
        db,
        f"""SELECT COALESCE(SUM(vsi.qty * vp.purchase_price), 0)
            FROM vendor_sale_items vsi
            JOIN vendor_sales vs ON vs.id = vsi.sale_id
            JOIN vendor_products vp ON vp.id = vsi.product_id
            WHERE vs.vendor_id=:vid AND vs.school_id=:sid {date_clause_sale}""",
        params,
    ) or 0

    outstanding = total_purchases - total_paid_to_vendor
    gross_profit = total_sales_revenue - cogs

    # Ledger — combine invoices, sales, payments into chronological entries
    invoices_rows = await _q(
        db,
        f"""SELECT 'invoice' AS type, invoice_date AS txn_date, invoice_number AS reference,
               total_amount AS debit, 0 AS credit
             FROM vendor_invoices WHERE vendor_id=:vid AND school_id=:sid {date_clause_inv}""",
        params,
    )
    payments_rows = await _q(
        db,
        f"""SELECT 'payment' AS type, payment_date AS txn_date, COALESCE(reference,'') AS reference,
               CASE WHEN direction='from_vendor' THEN amount ELSE 0 END AS debit,
               CASE WHEN direction='to_vendor' THEN amount ELSE 0 END AS credit
             FROM vendor_payments WHERE vendor_id=:vid AND school_id=:sid {date_clause_pay}""",
        params,
    )
    sales_rows = await _q(
        db,
        f"""SELECT 'sale' AS type, sale_date AS txn_date, id AS reference,
               0 AS debit, total_amount AS credit
             FROM vendor_sales WHERE vendor_id=:vid AND school_id=:sid {date_clause_sale}""",
        params,
    )

    ledger = sorted(
        invoices_rows + payments_rows + sales_rows,
        key=lambda x: str(x["txn_date"]),
    )

    # Compute running balance (positive = owed to vendor)
    balance = 0
    for entry in ledger:
        balance += entry["debit"] - entry["credit"]
        entry["running_balance"] = balance
        entry["debit_rs"] = _fmt(entry["debit"])
        entry["credit_rs"] = _fmt(entry["credit"])
        entry["running_balance_rs"] = _fmt(balance)

    return {
        "success": True,
        "data": {
            "summary": {
                "total_purchases_rs": _fmt(total_purchases),
                "total_paid_to_vendor_rs": _fmt(total_paid_to_vendor),
                "outstanding_to_vendor_rs": _fmt(outstanding),
                "total_sales_revenue_rs": _fmt(total_sales_revenue),
                "cost_of_goods_sold_rs": _fmt(cogs),
                "gross_profit_rs": _fmt(gross_profit),
            },
            "ledger": ledger,
        },
    }


# ─── Stock upsert helper ──────────────────────────────────────────────────────

async def _upsert_stock(db: AsyncSession, vendor_id: str, school_id: str, product_id: str, qty: int):
    existing = await _q(
        db, "SELECT id, qty_available FROM vendor_stock WHERE vendor_id=:v AND school_id=:s AND product_id=:p",
        {"v": vendor_id, "s": school_id, "p": product_id},
    )
    if existing:
        await db.execute(
            text("UPDATE vendor_stock SET qty_available=qty_available+:qty, updated_at=NOW() "
                 "WHERE vendor_id=:v AND school_id=:s AND product_id=:p"),
            {"qty": qty, "v": vendor_id, "s": school_id, "p": product_id},
        )
    else:
        await db.execute(
            text("INSERT INTO vendor_stock (id, vendor_id, school_id, product_id, qty_available, qty_reserved, created_at, updated_at) "
                 "VALUES (:id, :v, :s, :p, :qty, 0, NOW(), NOW())"),
            {"id": _new_id(), "v": vendor_id, "s": school_id, "p": product_id, "qty": qty},
        )
