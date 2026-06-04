"""API endpoints for the Advanced Fee Management (v2) feature."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_school_id, permission_required
from app.db.session import get_db
from app.models.auth import User
from app.repositories.fee_v2_repository import FeeV2Repository
from app.schemas.fees_v2 import (
    FeeCollectionCreate,
    FeeCollectionResponse,
    FeeCollectionItemResponse,
    FeeGroupCreate,
    FeeGroupResponse,
    FeeGroupUpdate,
    FeeMasterCreate,
    FeeMasterItemResponse,
    FeeMasterResponse,
    FeeMasterUpdate,
    FeeTypeCreate,
    FeeTypeResponse,
    FeeTypeUpdate,
    ReverseCollectionRequest,
    StudentFeeLedger,
    StudentFeeMasterAssignRequest,
    StudentFeeMasterAssignResponse,
)

router = APIRouter(prefix="/fees-v2", tags=["fees-v2"])


def _build_fee_type_response(row) -> dict:
    return {
        "id": row.id,
        "school_id": row.school_id,
        "name": row.name,
        "description": row.description,
        "is_active": row.is_active,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _build_fee_group_response(group, fee_types) -> dict:
    return {
        "id": group.id,
        "school_id": group.school_id,
        "name": group.name,
        "description": group.description,
        "is_active": group.is_active,
        "fee_types": [_build_fee_type_response(ft) for ft in fee_types],
        "created_at": group.created_at,
        "updated_at": group.updated_at,
    }


def _build_master_response(data: dict) -> dict:
    master = data["master"]
    return {
        "id": master.id,
        "school_id": master.school_id,
        "name": master.name,
        "class_id": master.class_id,
        "class_name": data.get("class_name"),
        "academic_year_id": master.academic_year_id,
        "academic_year_name": data.get("academic_year_name"),
        "fee_group_id": master.fee_group_id,
        "fee_group_name": data.get("fee_group_name"),
        "is_active": master.is_active,
        "items": [
            {
                "id": d["item"].id,
                "fee_type_id": d["item"].fee_type_id,
                "fee_type_name": d["fee_type_name"],
                "amount": d["item"].amount,
            }
            for d in data.get("items", [])
        ],
        "created_at": master.created_at,
        "updated_at": master.updated_at,
    }


def _build_collection_response(data: dict) -> dict:
    coll = data["collection"]
    return {
        "id": coll.id,
        "school_id": coll.school_id,
        "student_id": coll.student_id,
        "student_name": data.get("student_name"),
        "class_name": data.get("class_name"),
        "section_name": data.get("section_name"),
        "fee_master_id": coll.fee_master_id,
        "fee_master_name": data.get("fee_master_name"),
        "academic_year_id": coll.academic_year_id,
        "receipt_number": coll.receipt_number,
        "payment_date": coll.payment_date,
        "total_amount": coll.total_amount,
        "total_discount": coll.total_discount,
        "payment_method": coll.payment_method,
        "transaction_ref": coll.transaction_ref,
        "collected_by": coll.collected_by,
        "collected_by_name": data.get("collected_by_name"),
        "remarks": coll.remarks,
        "is_reversed": coll.is_reversed,
        "reversal_reason": coll.reversal_reason,
        "reversed_at": coll.reversed_at,
        "items": [
            {
                "id": d["item"].id,
                "fee_type_id": d["item"].fee_type_id,
                "fee_type_name": d["fee_type_name"],
                "amount_paid": d["item"].amount_paid,
                "discount_amount": d["item"].discount_amount,
                "discount_reason": d["item"].discount_reason,
            }
            for d in data.get("items", [])
        ],
        "created_at": coll.created_at,
    }


# ─── Fee Types ──────────────────────────────────────────────

@router.get("/fee-types", response_model=list[FeeTypeResponse])
async def list_fee_types(
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    return await repo.list_fee_types(school_id)


@router.post("/fee-types", response_model=FeeTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_fee_type(
    payload: FeeTypeCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "create")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    row = await repo.create_fee_type(school_id, payload)
    await db.commit()
    return row


@router.put("/fee-types/{fee_type_id}", response_model=FeeTypeResponse)
async def update_fee_type(
    fee_type_id: str,
    payload: FeeTypeUpdate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "update")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    row = await repo.get_fee_type(school_id, fee_type_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fee type not found")
    result = await repo.update_fee_type(row, payload)
    await db.commit()
    return result


@router.delete("/fee-types/{fee_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fee_type(
    fee_type_id: str,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "delete")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    row = await repo.get_fee_type(school_id, fee_type_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fee type not found")
    await repo.delete_fee_type(row)
    await db.commit()


# ─── Fee Groups ─────────────────────────────────────────────

@router.get("/fee-groups")
async def list_fee_groups(
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    groups = await repo.list_fee_groups(school_id)
    return [_build_fee_group_response(g["group"], g["fee_types"]) for g in groups]


@router.post("/fee-groups", status_code=status.HTTP_201_CREATED)
async def create_fee_group(
    payload: FeeGroupCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "create")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    row = await repo.create_fee_group(school_id, payload)
    fee_types = await repo.get_fee_group_types(str(row.id))
    await db.commit()
    return _build_fee_group_response(row, fee_types)


@router.put("/fee-groups/{group_id}")
async def update_fee_group(
    group_id: str,
    payload: FeeGroupUpdate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "update")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    row = await repo.get_fee_group(school_id, group_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fee group not found")
    updated = await repo.update_fee_group(row, payload)
    fee_types = await repo.get_fee_group_types(str(updated.id))
    await db.commit()
    return _build_fee_group_response(updated, fee_types)


@router.delete("/fee-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fee_group(
    group_id: str,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "delete")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    row = await repo.get_fee_group(school_id, group_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fee group not found")
    await repo.delete_fee_group(row)
    await db.commit()


# ─── Fee Masters ────────────────────────────────────────────

@router.get("/fee-masters")
async def list_fee_masters(
    class_id: Optional[str] = Query(None),
    academic_year_id: Optional[str] = Query(None),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    masters = await repo.list_fee_masters(school_id, class_id=class_id, year_id=academic_year_id)
    return [_build_master_response(m) for m in masters]


@router.post("/fee-masters", status_code=status.HTTP_201_CREATED)
async def create_fee_master(
    payload: FeeMasterCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "create")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    row = await repo.create_fee_master(school_id, payload)
    masters = await repo.list_fee_masters(school_id)
    await db.commit()
    # find the one just created
    for m in masters:
        if str(m["master"].id) == str(row.id):
            return _build_master_response(m)
    return {"id": str(row.id)}


@router.put("/fee-masters/{master_id}")
async def update_fee_master(
    master_id: str,
    payload: FeeMasterUpdate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "update")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    row = await repo.get_fee_master(school_id, master_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fee master not found")
    await repo.update_fee_master(row, payload)
    masters = await repo.list_fee_masters(school_id)
    await db.commit()
    for m in masters:
        if str(m["master"].id) == master_id:
            return _build_master_response(m)
    return {"id": master_id}


@router.delete("/fee-masters/{master_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fee_master(
    master_id: str,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "delete")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    row = await repo.get_fee_master(school_id, master_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fee master not found")
    await repo.delete_fee_master(row)
    await db.commit()


# ─── Student Assignments ────────────────────────────────────

@router.get("/assignments")
async def list_assignments(
    academic_year_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    rows = await repo.list_assignments(school_id, year_id=academic_year_id, class_id=class_id)
    return [
        {
            "id": r["assignment"].id,
            "school_id": r["assignment"].school_id,
            "student_id": r["assignment"].student_id,
            "student_name": r["student_name"],
            "fee_master_id": r["assignment"].fee_master_id,
            "fee_master_name": r["fee_master_name"],
            "academic_year_id": r["assignment"].academic_year_id,
            "created_at": r["assignment"].created_at,
        }
        for r in rows
    ]


@router.post("/assignments", status_code=status.HTTP_201_CREATED)
async def assign_fee_master(
    payload: StudentFeeMasterAssignRequest,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("fees", "create")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    created = await repo.assign_fee_master(school_id, payload, str(current_user.id))
    await db.commit()
    return {"assigned": len(created), "message": f"Assigned fee master to {len(created)} student(s)"}


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_assignment(
    assignment_id: str,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "delete")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    row = await repo.get_assignment(school_id, assignment_id)
    if not row:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await repo.remove_assignment(row)
    await db.commit()


# ─── Fee Ledger ─────────────────────────────────────────────

@router.get("/ledger/{student_id}")
async def get_student_ledger(
    student_id: str,
    academic_year_id: str = Query(...),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    ledgers = await repo.get_student_ledger(school_id, student_id, academic_year_id)
    # Return list of all fee master ledgers assigned to this student
    return ledgers


# ─── Fee Collection ──────────────────────────────────────────

@router.get("/collections")
async def list_collections(
    student_id: Optional[str] = Query(None),
    academic_year_id: Optional[str] = Query(None),
    include_reversed: bool = Query(False),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    rows = await repo.list_collections(
        school_id,
        student_id=student_id,
        year_id=academic_year_id,
        include_reversed=include_reversed,
    )
    return [_build_collection_response(r) for r in rows]


@router.post("/collections", status_code=status.HTTP_201_CREATED)
async def collect_fee(
    payload: FeeCollectionCreate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("fees", "create")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    coll = await repo.collect_fee(school_id, payload, str(current_user.id))
    # Build response BEFORE commit — ORM objects expire after commit in async mode
    rows = await repo.list_collections(school_id, student_id=payload.student_id, include_reversed=True)
    response_data = None
    for r in rows:
        if str(r["collection"].id) == str(coll.id):
            response_data = _build_collection_response(r)
            break
    if response_data is None:
        response_data = {"id": str(coll.id), "receipt_number": coll.receipt_number}
    await db.commit()
    return response_data


@router.post("/collections/{collection_id}/reverse")
async def reverse_collection(
    collection_id: str,
    payload: ReverseCollectionRequest,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("fees", "update")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeV2Repository(db)
    row = await repo.get_collection(school_id, collection_id)
    if not row:
        raise HTTPException(status_code=404, detail="Collection not found")
    if row.is_reversed:
        raise HTTPException(status_code=400, detail="This collection is already reversed")
    await repo.reverse_collection(row, payload.reason, str(current_user.id))
    await db.commit()
    return {"success": True, "message": "Collection reversed successfully"}


# ─── Fee Receipt PDF ─────────────────────────────────────────────────────────

@router.get("/collections/{collection_id}/receipt/pdf")
async def download_fee_receipt_pdf(
    collection_id: str,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Generate and return a fee receipt PDF for a given collection."""
    from fastapi.responses import Response as FastAPIResponse
    from app.services.pdf_service import generate_fee_receipt_pdf
    from app.repositories.school_repository import SchoolRepository

    repo = FeeV2Repository(db)
    row = await repo.get_collection(school_id, collection_id)
    if not row:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Load full collection data via list_collections
    rows = await repo.list_collections(school_id, include_reversed=True)
    coll_data = None
    for r in rows:
        if str(r["collection"].id) == collection_id:
            coll_data = _build_collection_response(r)
            break

    if not coll_data:
        raise HTTPException(status_code=404, detail="Collection detail not found")

    # Load school info
    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(school_id)
    school_name = school.name if school else "School"
    school_address = getattr(school, "address", None) if school else None
    school_phone = getattr(school, "phone", None) if school else None

    pdf_data = {
        "school_name": school_name,
        "school_address": school_address,
        "school_phone": school_phone,
        "receipt_number": coll_data.get("receipt_number"),
        "payment_date": coll_data.get("payment_date"),
        "payment_method": coll_data.get("payment_method"),
        "transaction_ref": coll_data.get("transaction_ref"),
        "student_name": coll_data.get("student_name"),
        "admission_number": "",
        "class_name": coll_data.get("class_name"),
        "section_name": coll_data.get("section_name"),
        "collected_by_name": coll_data.get("collected_by_name"),
        "items": coll_data.get("items", []),
        "total_amount": coll_data.get("total_amount", 0),
        "total_discount": coll_data.get("total_discount", 0),
        "remarks": coll_data.get("remarks"),
    }

    pdf_bytes = generate_fee_receipt_pdf(pdf_data)
    receipt_no = coll_data.get("receipt_number", collection_id)
    filename = f"fee_receipt_{receipt_no}.pdf"

    return FastAPIResponse(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

