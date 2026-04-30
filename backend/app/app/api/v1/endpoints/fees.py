from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_school_id, permission_required
from app.db.session import get_db
from app.models.auth import User
from app.models.fees import InvoiceStatus
from app.repositories.fee_repository import FeeRepository
from app.schemas.phase8 import (
    AssignFeesToStudentsRequest,
    CollectionSummary,
    CollectFeeRequest,
    DefaulterEntry,
    FeeCategoryCreate,
    FeeCategoryResponse,
    FeeCategoryUpdate,
    FeeClearanceResponse,
    FeeDiscountCreate,
    FeeDiscountResponse,
    FeeDiscountUpdate,
    FeeInvoiceResponse,
    FeePaymentResponse,
    FeeRolloverRequest,
    FeeStructureCreate,
    FeeStructureResponse,
    FineConfigurationCreate,
    FineConfigurationResponse,
    FineConfigurationUpdate,
    InvoiceGenerationRequest,
    OnlinePaymentCallbackRequest,
    OnlinePaymentInitRequest,
    OnlinePaymentInitResponse,
    ReversePaymentRequest,
    StudentDiscountCreate,
    StudentDiscountResponse,
    StudentFeeStatement,
)
from app.services.fee_service import FeeService

router = APIRouter()


@router.get("/categories", response_model=list[FeeCategoryResponse])
async def list_fee_categories(
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeRepository(db)
    return await repo.list_categories(school_id)


@router.post("/categories", response_model=FeeCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_fee_category(
    payload: FeeCategoryCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "create")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeRepository(db)
    return await repo.create_category(school_id, payload.model_dump())


@router.put("/categories/{category_id}", response_model=FeeCategoryResponse)
async def update_fee_category(
    category_id: str,
    payload: FeeCategoryUpdate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "update")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeRepository(db)
    row = await repo.get_category(school_id, category_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fee category not found")
    return await repo.update_category(row, payload.model_dump(exclude_unset=True))


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fee_category(
    category_id: str,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "delete")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeRepository(db)
    row = await repo.get_category(school_id, category_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fee category not found")
    await repo.delete_category(row)


@router.get("/structures", response_model=list[FeeStructureResponse])
async def list_fee_structures(
    academic_year_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeRepository(db)
    rows = await repo.list_structures(school_id, academic_year_id, class_id)
    return [
        FeeStructureResponse(
            id=str(structure.id),
            school_id=str(structure.school_id),
            academic_year_id=str(structure.academic_year_id),
            class_id=str(structure.class_id),
            fee_category_id=str(structure.fee_category_id),
            amount=int(structure.amount),
            frequency=structure.frequency,
            due_day=structure.due_day,
            is_active=structure.is_active,
            created_at=structure.created_at,
            updated_at=structure.updated_at,
            fee_category_name=category_name,
        )
        for structure, category_name in rows
    ]


@router.post("/structures", response_model=list[FeeStructureResponse])
async def upsert_fee_structures(
    payload: FeeStructureCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "create")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeRepository(db)
    rows = await repo.upsert_structures(
        school_id=school_id,
        academic_year_id=payload.academic_year_id,
        class_id=payload.class_id,
        items=[item.model_dump() for item in payload.items],
    )
    mapped_rows = await repo.list_structures(school_id, payload.academic_year_id, payload.class_id)
    response = []
    for structure, category_name in mapped_rows:
        if str(structure.id) not in {str(item.id) for item in rows}:
            continue
        response.append(
            FeeStructureResponse(
                id=str(structure.id),
                school_id=str(structure.school_id),
                academic_year_id=str(structure.academic_year_id),
                class_id=str(structure.class_id),
                fee_category_id=str(structure.fee_category_id),
                amount=int(structure.amount),
                frequency=structure.frequency,
                due_day=structure.due_day,
                is_active=structure.is_active,
                created_at=structure.created_at,
                updated_at=structure.updated_at,
                fee_category_name=category_name,
            )
        )
    return response


@router.get("/discounts", response_model=list[FeeDiscountResponse])
async def list_fee_discounts(
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeRepository(db)
    return await repo.list_discounts(school_id)


@router.post("/discounts", response_model=FeeDiscountResponse, status_code=status.HTTP_201_CREATED)
async def create_fee_discount(
    payload: FeeDiscountCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "create")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeRepository(db)
    return await repo.create_discount(school_id, payload.model_dump())


@router.put("/discounts/{discount_id}", response_model=FeeDiscountResponse)
async def update_fee_discount(
    discount_id: str,
    payload: FeeDiscountUpdate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "update")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeRepository(db)
    row = await repo.get_discount(school_id, discount_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fee discount not found")
    return await repo.update_discount(row, payload.model_dump(exclude_unset=True))


@router.delete("/discounts/{discount_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fee_discount(
    discount_id: str,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "delete")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeRepository(db)
    row = await repo.get_discount(school_id, discount_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fee discount not found")
    await repo.delete_discount(row)


@router.post("/assign", response_model=dict)
async def assign_fees_to_students(
    payload: AssignFeesToStudentsRequest,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "manage")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    return await service.assign_fees_to_students(school_id, payload)


@router.post("/invoices/generate", response_model=dict)
async def generate_invoices(
    payload: InvoiceGenerationRequest,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "manage")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    return await service.generate_invoices(school_id, payload)


@router.get("/invoices", response_model=list[FeeInvoiceResponse])
async def list_invoices(
    academic_year_id: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    section_id: Optional[str] = Query(None),
    status: Optional[InvoiceStatus] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    return await service.list_invoice_responses(
        school_id=school_id,
        academic_year_id=academic_year_id,
        student_id=student_id,
        section_id=section_id,
        status=status,
        month=month,
        year=year,
    )


@router.get("/invoices/{invoice_id}", response_model=FeeInvoiceResponse)
async def get_invoice(
    invoice_id: str,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    try:
        return await service.get_invoice_response(school_id, invoice_id)
    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex))


@router.post("/payments", response_model=FeePaymentResponse, status_code=status.HTTP_201_CREATED)
async def collect_fee_payment(
    payload: CollectFeeRequest,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("fees", "collect")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    try:
        return await service.collect_fee(school_id, payload, str(current_user.id))
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/payments", response_model=list[FeePaymentResponse])
async def list_fee_payments(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    invoice_id: Optional[str] = Query(None),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    return await service.list_payments(school_id, from_date, to_date, invoice_id)


@router.post("/payments/{payment_id}/reverse", response_model=dict)
async def reverse_fee_payment(
    payment_id: str,
    payload: ReversePaymentRequest,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "approve")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    try:
        return await service.reverse_payment(school_id, payment_id, payload.reason)
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/students/{student_id}/discounts", response_model=StudentDiscountResponse, status_code=status.HTTP_201_CREATED)
async def assign_student_discount(
    student_id: str,
    payload: StudentDiscountCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "manage")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    try:
        return await service.assign_student_discount(school_id, student_id, payload)
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/students/{student_id}/discounts", response_model=list[StudentDiscountResponse])
async def list_student_discounts(
    student_id: str,
    academic_year_id: Optional[str] = Query(None),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    return await service.list_student_discounts(school_id, student_id, academic_year_id)


@router.delete("/students/{student_id}/discounts/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_student_discount(
    student_id: str,
    assignment_id: str,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "manage")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    try:
        await service.remove_student_discount(school_id, assignment_id)
    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex))


@router.get("/students/{student_id}/clearance", response_model=FeeClearanceResponse)
async def fee_clearance(
    student_id: str,
    academic_year_id: str,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    try:
        return await service.check_fee_clearance(school_id, student_id, academic_year_id)
    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex))


@router.post("/structures/rollover", response_model=dict)
async def rollover_fee_structures(
    payload: FeeRolloverRequest,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "manage")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    return await service.rollover_fee_structures(school_id, payload)


@router.get("/students/{student_id}/statement", response_model=StudentFeeStatement)
async def get_student_statement(
    student_id: str,
    academic_year_id: str,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "report")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    try:
        return await service.get_student_statement(school_id, student_id, academic_year_id)
    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex))


@router.get("/reports/defaulters", response_model=list[DefaulterEntry])
async def list_defaulters(
    academic_year_id: str,
    as_of_date: date = Query(default_factory=date.today),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "report")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    return await service.list_defaulters(school_id, academic_year_id, as_of_date)


@router.get("/reports/daily-collection", response_model=CollectionSummary)
async def daily_collection_report(
    day: date = Query(default_factory=date.today),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "report")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    return await service.daily_collection(school_id, day)


@router.get("/reports/monthly-collection", response_model=CollectionSummary)
async def monthly_collection_report(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000, le=2100),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "report")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    return await service.monthly_collection(school_id, month, year)


@router.get("/fines", response_model=FineConfigurationResponse | None)
async def get_fine_configuration(
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "view")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeRepository(db)
    return await repo.get_fine_configuration(school_id)


@router.post("/fines", response_model=FineConfigurationResponse)
async def upsert_fine_configuration(
    payload: FineConfigurationCreate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "manage")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    return await service.upsert_fine_configuration(school_id, payload)


@router.put("/fines", response_model=FineConfigurationResponse)
async def update_fine_configuration(
    payload: FineConfigurationUpdate,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "manage")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    return await service.upsert_fine_configuration(school_id, payload)


@router.post("/fines/apply", response_model=dict)
async def apply_fines(
    as_of_date: date = Query(default_factory=date.today),
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "manage")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    return await service.apply_fines(school_id, as_of_date)


@router.post("/online/init", response_model=OnlinePaymentInitResponse)
async def init_online_payment(
    payload: OnlinePaymentInitRequest,
    school_id: str = Depends(get_school_id),
    _: User = Depends(permission_required("fees", "pay")),
    db: AsyncSession = Depends(get_db),
):
    repo = FeeRepository(db)
    invoice = await repo.get_invoice(school_id, payload.invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if payload.amount > int(invoice.balance_amount):
        raise HTTPException(status_code=400, detail="Amount exceeds invoice balance")

    service = FeeService(db)
    return await service.init_online_payment(payload)


@router.post("/online/callback", response_model=FeePaymentResponse)
async def online_payment_callback(
    payload: OnlinePaymentCallbackRequest,
    school_id: str = Depends(get_school_id),
    system_user: User = Depends(permission_required("fees", "collect")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    try:
        return await service.collect_fee(
            school_id,
            CollectFeeRequest(
                invoice_id=payload.invoice_id,
                amount=payload.amount,
                payment_date=payload.payment_date,
                payment_method="online",
                transaction_id=payload.transaction_id,
                remarks=f"gateway_order={payload.order_id}",
            ),
            str(system_user.id),
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

