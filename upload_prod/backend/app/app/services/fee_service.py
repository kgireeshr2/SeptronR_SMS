from datetime import date
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fees import InvoiceStatus
from app.repositories.fee_repository import FeeRepository
from app.schemas.phase8 import (
    AssignFeesToStudentsRequest,
    CollectionSummary,
    CollectFeeRequest,
    DefaulterEntry,
    FeeClearanceResponse,
    FeeInvoiceItemResponse,
    FeeInvoiceResponse,
    FeePaymentResponse,
    FeeRolloverRequest,
    FineConfigurationCreate,
    FineConfigurationUpdate,
    InvoiceGenerationRequest,
    OnlinePaymentInitRequest,
    OnlinePaymentInitResponse,
    StudentDiscountCreate,
    StudentDiscountResponse,
    StudentFeeStatement,
)


class FeeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = FeeRepository(db)

    async def assign_fees_to_students(self, school_id: str, payload: AssignFeesToStudentsRequest) -> dict:
        assigned, skipped = await self.repo.assign_to_students(
            school_id=school_id,
            academic_year_id=payload.academic_year_id,
            class_id=payload.class_id,
            discount_map=payload.discount_map,
        )
        return {"assigned": assigned, "skipped": skipped}

    async def generate_invoices(self, school_id: str, payload: InvoiceGenerationRequest) -> dict:
        created, skipped = await self.repo.generate_monthly_invoices(
            school_id=school_id,
            academic_year_id=payload.academic_year_id,
            month=payload.month,
            year=payload.year,
            class_id=payload.class_id,
            student_id=payload.student_id,
        )
        return {"created": created, "skipped": skipped}

    async def get_invoice_response(self, school_id: str, invoice_id: str) -> FeeInvoiceResponse:
        invoice = await self.repo.get_invoice(school_id, invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        return await self._to_invoice_response(school_id, invoice)

    async def list_invoice_responses(
        self,
        school_id: str,
        academic_year_id: str | None = None,
        student_id: str | None = None,
        section_id: str | None = None,
        status: InvoiceStatus | None = None,
        month: int | None = None,
        year: int | None = None,
    ) -> list[FeeInvoiceResponse]:
        invoices = await self.repo.list_invoices(
            school_id=school_id,
            academic_year_id=academic_year_id,
            student_id=student_id,
            section_id=section_id,
            status=status,
            month=month,
            year=year,
        )
        output = []
        for invoice in invoices:
            output.append(await self._to_invoice_response(school_id, invoice))
        return output

    async def collect_fee(self, school_id: str, payload: CollectFeeRequest, collected_by: str) -> FeePaymentResponse:
        payment = await self.repo.collect_payment(
            school_id=school_id,
            invoice_id=payload.invoice_id,
            amount=payload.amount,
            payment_date=payload.payment_date,
            payment_method=payload.payment_method,
            collected_by=collected_by,
            transaction_id=payload.transaction_id,
            remarks=payload.remarks,
        )
        invoice_number, student_id, student_name = await self.repo.get_invoice_party(school_id, payload.invoice_id)
        return FeePaymentResponse(
            id=str(payment.id),
            school_id=str(payment.school_id),
            invoice_id=str(payment.invoice_id),
            invoice_number=invoice_number,
            student_id=student_id,
            student_name=student_name,
            amount=int(payment.amount),
            payment_date=payment.payment_date,
            payment_method=payment.payment_method,
            transaction_id=payment.transaction_id,
            receipt_number=payment.receipt_number,
            collected_by=str(payment.collected_by),
            remarks=payment.remarks,
            is_reversed=payment.is_reversed,
            reversal_reason=payment.reversal_reason,
            created_at=payment.created_at,
        )

    async def list_payments(
        self,
        school_id: str,
        from_date: date | None = None,
        to_date: date | None = None,
        invoice_id: str | None = None,
    ) -> list[FeePaymentResponse]:
        rows = await self.repo.list_payments(school_id, from_date, to_date, invoice_id)
        out: list[FeePaymentResponse] = []
        for payment in rows:
            invoice_number, student_id, student_name = await self.repo.get_invoice_party(school_id, str(payment.invoice_id))
            out.append(
                FeePaymentResponse(
                    id=str(payment.id),
                    school_id=str(payment.school_id),
                    invoice_id=str(payment.invoice_id),
                    invoice_number=invoice_number,
                    student_id=student_id,
                    student_name=student_name,
                    amount=int(payment.amount),
                    payment_date=payment.payment_date,
                    payment_method=payment.payment_method,
                    transaction_id=payment.transaction_id,
                    receipt_number=payment.receipt_number,
                    collected_by=str(payment.collected_by),
                    remarks=payment.remarks,
                    is_reversed=payment.is_reversed,
                    reversal_reason=payment.reversal_reason,
                    created_at=payment.created_at,
                )
            )
        return out

    async def reverse_payment(self, school_id: str, payment_id: str, reason: str) -> dict:
        payment, invoice = await self.repo.reverse_payment(school_id, payment_id, reason)
        return {
            "message": "Payment reversed",
            "invoice_id": str(invoice.id),
            "payment_id": str(payment.id),
            "invoice_status": invoice.status,
        }

    async def get_student_statement(self, school_id: str, student_id: str, academic_year_id: str) -> StudentFeeStatement:
        statement = await self.repo.get_student_statement(school_id, student_id, academic_year_id)
        invoices = []
        for invoice in statement["invoices"]:
            invoices.append(await self._to_invoice_response(school_id, invoice))
        return StudentFeeStatement(
            student_id=statement["student_id"],
            student_name=statement["student_name"],
            academic_year_id=statement["academic_year_id"],
            total_amount=statement["total_amount"],
            total_paid=statement["total_paid"],
            total_due=statement["total_due"],
            invoices=invoices,
        )

    async def list_defaulters(self, school_id: str, academic_year_id: str, as_of_date: date) -> list[DefaulterEntry]:
        rows = await self.repo.list_defaulters(school_id, academic_year_id, as_of_date)
        return [DefaulterEntry(**row) for row in rows]

    async def daily_collection(self, school_id: str, day: date) -> CollectionSummary:
        data = await self.repo.daily_collection_summary(school_id, day)
        return CollectionSummary(**data)

    async def monthly_collection(self, school_id: str, month: int, year: int) -> CollectionSummary:
        data = await self.repo.monthly_collection_summary(school_id, month, year)
        return CollectionSummary(**data)

    async def upsert_fine_configuration(self, school_id: str, payload: FineConfigurationCreate | FineConfigurationUpdate):
        return await self.repo.upsert_fine_configuration(
            school_id,
            payload.model_dump(exclude_unset=True),
        )

    async def apply_fines(self, school_id: str, as_of_date: date) -> dict:
        marked = await self.repo.update_overdue_flags(school_id, as_of_date)
        fined = await self.repo.apply_fine(school_id, as_of_date)
        return {"overdue_marked": marked, "fine_applied": fined}

    async def init_online_payment(self, payload: OnlinePaymentInitRequest) -> OnlinePaymentInitResponse:
        order_id = f"{payload.gateway.upper()}_{uuid4().hex[:18]}"
        return OnlinePaymentInitResponse(order_id=order_id, gateway=payload.gateway, amount=payload.amount)

    async def assign_student_discount(
        self, school_id: str, student_id: str, payload: StudentDiscountCreate
    ) -> StudentDiscountResponse:
        row = await self.repo.assign_student_discount(
            school_id=school_id,
            student_id=student_id,
            discount_id=payload.discount_id,
            academic_year_id=payload.academic_year_id,
            remarks=payload.remarks,
        )
        rows = await self.repo.list_student_discounts(school_id, student_id, payload.academic_year_id)
        match = next((r for r in rows if str(r[0].id) == str(row.id)), None)
        if not match:
            raise ValueError("Could not fetch assigned discount")
        sda, d_name, d_type, d_value, d_nature = match
        return StudentDiscountResponse(
            id=str(sda.id),
            student_id=str(sda.student_id),
            discount_id=str(sda.discount_id),
            discount_name=d_name,
            discount_type=d_type,
            discount_value=float(d_value),
            discount_nature=d_nature,
            academic_year_id=str(sda.academic_year_id),
            remarks=sda.remarks,
            created_at=sda.created_at,
        )

    async def list_student_discounts(
        self, school_id: str, student_id: str, academic_year_id: str | None = None
    ) -> list[StudentDiscountResponse]:
        rows = await self.repo.list_student_discounts(school_id, student_id, academic_year_id)
        out = []
        for sda, d_name, d_type, d_value, d_nature in rows:
            out.append(StudentDiscountResponse(
                id=str(sda.id),
                student_id=str(sda.student_id),
                discount_id=str(sda.discount_id),
                discount_name=d_name,
                discount_type=d_type,
                discount_value=float(d_value),
                discount_nature=d_nature,
                academic_year_id=str(sda.academic_year_id),
                remarks=sda.remarks,
                created_at=sda.created_at,
            ))
        return out

    async def remove_student_discount(self, school_id: str, assignment_id: str) -> None:
        await self.repo.remove_student_discount(school_id, assignment_id)

    async def check_fee_clearance(
        self, school_id: str, student_id: str, academic_year_id: str
    ) -> FeeClearanceResponse:
        data = await self.repo.check_clearance(school_id, student_id, academic_year_id)
        return FeeClearanceResponse(**data)

    async def rollover_fee_structures(
        self, school_id: str, payload: FeeRolloverRequest
    ) -> dict:
        created, skipped = await self.repo.rollover_structures(
            school_id, payload.from_year_id, payload.to_year_id
        )
        return {"created": created, "skipped": skipped}

    async def _to_invoice_response(self, school_id: str, invoice) -> FeeInvoiceResponse:
        items_rows = await self.repo.get_invoice_items(str(invoice.id))
        item_models = [
            FeeInvoiceItemResponse(
                id=str(item.id),
                fee_category_id=str(item.fee_category_id),
                fee_category_name=category_name,
                amount=int(item.amount),
                discount_amt=int(item.discount_amt),
                fine_applied=int(item.fine_applied),
            )
            for item, category_name in items_rows
        ]

        _, student_id, student_name = await self.repo.get_invoice_party(school_id, str(invoice.id))
        class_name, section_name = await self.repo.get_invoice_class_section(
            str(invoice.id), str(invoice.academic_year_id)
        )
        return FeeInvoiceResponse(
            id=str(invoice.id),
            school_id=str(invoice.school_id),
            student_id=str(invoice.student_id),
            student_name=student_name,
            academic_year_id=str(invoice.academic_year_id),
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            status=invoice.status,
            total_amount=int(invoice.total_amount),
            paid_amount=int(invoice.paid_amount),
            balance_amount=int(invoice.balance_amount),
            class_name=class_name,
            section_name=section_name,
            items=item_models,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
        )

