from datetime import date
from calendar import monthrange
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import and_, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classes import Class, Section
from app.models.fees import (
    FeeCategory,
    FeeDiscount,
    FeeInvoice,
    FeeInvoiceItem,
    FeeStructure,
    FineCalcType,
    FineConfiguration,
    InvoiceStatus,
    StudentDiscountAssignment,
    StudentFeeAssignment,
    FeePayment,
)
from app.models.students import Student, StudentEnrollment


class FeeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_categories(self, school_id: str) -> list[FeeCategory]:
        result = await self.db.execute(
            select(FeeCategory)
            .where(FeeCategory.school_id == school_id)
            .order_by(FeeCategory.name.asc())
        )
        return list(result.scalars().all())

    async def get_category(self, school_id: str, category_id: str) -> FeeCategory | None:
        result = await self.db.execute(
            select(FeeCategory).where(FeeCategory.school_id == school_id, FeeCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def create_category(self, school_id: str, data: dict) -> FeeCategory:
        row = FeeCategory(school_id=school_id, **data)
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def update_category(self, row: FeeCategory, data: dict) -> FeeCategory:
        for key, value in data.items():
            setattr(row, key, value)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def delete_category(self, row: FeeCategory) -> None:
        await self.db.delete(row)
        await self.db.flush()

    async def list_structures(
        self,
        school_id: str,
        academic_year_id: str | None = None,
        class_id: str | None = None,
    ) -> list[tuple[FeeStructure, str]]:
        query = (
            select(FeeStructure, FeeCategory.name)
            .join(FeeCategory, FeeCategory.id == FeeStructure.fee_category_id)
            .where(FeeStructure.school_id == school_id)
            .order_by(FeeCategory.name.asc())
        )
        if academic_year_id:
            query = query.where(FeeStructure.academic_year_id == academic_year_id)
        if class_id:
            query = query.where(FeeStructure.class_id == class_id)

        result = await self.db.execute(query)
        return list(result.all())

    async def upsert_structures(
        self,
        school_id: str,
        academic_year_id: str,
        class_id: str,
        items: list[dict],
    ) -> list[FeeStructure]:
        created_or_updated: list[FeeStructure] = []
        for item in items:
            result = await self.db.execute(
                select(FeeStructure).where(
                    FeeStructure.school_id == school_id,
                    FeeStructure.academic_year_id == academic_year_id,
                    FeeStructure.class_id == class_id,
                    FeeStructure.fee_category_id == item["fee_category_id"],
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.amount = item["amount"]
                existing.frequency = item["frequency"]
                existing.due_day = item.get("due_day")
                existing.is_active = item.get("is_active", True)
                created_or_updated.append(existing)
            else:
                row = FeeStructure(
                    school_id=school_id,
                    academic_year_id=academic_year_id,
                    class_id=class_id,
                    fee_category_id=item["fee_category_id"],
                    amount=item["amount"],
                    frequency=item["frequency"],
                    due_day=item.get("due_day"),
                    is_active=item.get("is_active", True),
                )
                self.db.add(row)
                created_or_updated.append(row)
        await self.db.flush()
        for row in created_or_updated:
            await self.db.refresh(row)
        return created_or_updated

    async def list_discounts(self, school_id: str) -> list[FeeDiscount]:
        result = await self.db.execute(
            select(FeeDiscount).where(FeeDiscount.school_id == school_id).order_by(FeeDiscount.name.asc())
        )
        return list(result.scalars().all())

    async def get_discount(self, school_id: str, discount_id: str) -> FeeDiscount | None:
        result = await self.db.execute(
            select(FeeDiscount).where(FeeDiscount.school_id == school_id, FeeDiscount.id == discount_id)
        )
        return result.scalar_one_or_none()

    async def create_discount(self, school_id: str, data: dict) -> FeeDiscount:
        row = FeeDiscount(school_id=school_id, **data)
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def update_discount(self, row: FeeDiscount, data: dict) -> FeeDiscount:
        for key, value in data.items():
            setattr(row, key, value)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def delete_discount(self, row: FeeDiscount) -> None:
        await self.db.delete(row)
        await self.db.flush()

    async def assign_to_students(
        self,
        school_id: str,
        academic_year_id: str,
        class_id: str | None,
        discount_map: dict[str, str],
    ) -> tuple[int, int]:
        structures_query = select(FeeStructure).where(
            FeeStructure.school_id == school_id,
            FeeStructure.academic_year_id == academic_year_id,
            FeeStructure.is_active == True,
        )
        if class_id:
            structures_query = structures_query.where(FeeStructure.class_id == class_id)
        structures_result = await self.db.execute(structures_query)
        structures = list(structures_result.scalars().all())

        enroll_query = select(StudentEnrollment.student_id, StudentEnrollment.class_id).where(
            StudentEnrollment.school_id == school_id,
            StudentEnrollment.academic_year_id == academic_year_id,
            StudentEnrollment.is_current == True,
        )
        if class_id:
            enroll_query = enroll_query.where(StudentEnrollment.class_id == class_id)
        enroll_result = await self.db.execute(enroll_query)
        enrollments = list(enroll_result.all())

        structure_map: dict[str, list[FeeStructure]] = {}
        for structure in structures:
            structure_map.setdefault(str(structure.class_id), []).append(structure)

        assigned = 0
        skipped = 0
        for student_id, enrolled_class_id in enrollments:
            for structure in structure_map.get(str(enrolled_class_id), []):
                existing_result = await self.db.execute(
                    select(StudentFeeAssignment).where(
                        StudentFeeAssignment.school_id == school_id,
                        StudentFeeAssignment.student_id == student_id,
                        StudentFeeAssignment.academic_year_id == academic_year_id,
                        StudentFeeAssignment.fee_structure_id == structure.id,
                    )
                )
                existing = existing_result.scalar_one_or_none()
                if existing:
                    skipped += 1
                    discount_id = discount_map.get(str(student_id))
                    if discount_id:
                        existing.discount_id = discount_id
                    continue

                assignment = StudentFeeAssignment(
                    school_id=school_id,
                    student_id=student_id,
                    fee_structure_id=structure.id,
                    discount_id=discount_map.get(str(student_id)),
                    custom_amount=None,
                    academic_year_id=academic_year_id,
                )
                self.db.add(assignment)
                assigned += 1

        await self.db.flush()
        return assigned, skipped

    async def _next_invoice_number(self, school_id: str, month: int, year: int) -> str:
        prefix = f"INV-{year}{month:02d}-"
        count_result = await self.db.execute(
            select(func.count(FeeInvoice.id)).where(
                FeeInvoice.school_id == school_id,
                FeeInvoice.invoice_number.like(f"{prefix}%"),
            )
        )
        current_count = int(count_result.scalar() or 0)
        return f"{prefix}{current_count + 1:05d}"

    def _calculate_discount(self, base_amount: int, discount: FeeDiscount | None) -> int:
        if not discount:
            return 0
        if str(discount.type) == "fixed":
            return min(base_amount, int(Decimal(discount.value)))
        pct = float(discount.value)
        discount_amount = int(round(base_amount * pct / 100.0))
        return min(base_amount, max(discount_amount, 0))

    async def generate_monthly_invoices(
        self,
        school_id: str,
        academic_year_id: str,
        month: int,
        year: int,
        class_id: str | None = None,
        student_id: str | None = None,
    ) -> tuple[int, int]:
        assign_query = (
            select(StudentFeeAssignment, FeeStructure)
            .join(FeeStructure, FeeStructure.id == StudentFeeAssignment.fee_structure_id)
            .where(
                StudentFeeAssignment.school_id == school_id,
                StudentFeeAssignment.academic_year_id == academic_year_id,
                FeeStructure.is_active == True,
            )
        )
        if class_id:
            assign_query = assign_query.where(FeeStructure.class_id == class_id)
        if student_id:
            assign_query = assign_query.where(StudentFeeAssignment.student_id == student_id)

        rows = list((await self.db.execute(assign_query)).all())
        if not rows:
            return 0, 0

        grouped: dict[str, list[tuple[StudentFeeAssignment, FeeStructure]]] = {}
        for assignment, structure in rows:
            grouped.setdefault(str(assignment.student_id), []).append((assignment, structure))

        created = 0
        skipped = 0
        for sid, assignments in grouped.items():
            existing_result = await self.db.execute(
                select(FeeInvoice.id).where(
                    FeeInvoice.school_id == school_id,
                    FeeInvoice.student_id == sid,
                    FeeInvoice.academic_year_id == academic_year_id,
                    extract("month", FeeInvoice.invoice_date) == month,
                    extract("year", FeeInvoice.invoice_date) == year,
                    FeeInvoice.status != InvoiceStatus.cancelled,
                )
            )
            if existing_result.scalar_one_or_none():
                skipped += 1
                continue

            due_day = next((item[1].due_day for item in assignments if item[1].due_day), 10) or 10
            last_day = monthrange(year, month)[1]
            due_day = max(1, min(due_day, last_day))
            invoice_date = date(year, month, 1)
            due_date = date(year, month, due_day)

            invoice = FeeInvoice(
                school_id=school_id,
                student_id=sid,
                academic_year_id=academic_year_id,
                invoice_number=await self._next_invoice_number(school_id, month, year),
                invoice_date=invoice_date,
                due_date=due_date,
                status=InvoiceStatus.unpaid,
                total_amount=0,
                paid_amount=0,
            )
            self.db.add(invoice)
            await self.db.flush()

            invoice_total = 0
            for assignment, structure in assignments:
                discount = None
                if assignment.discount_id:
                    discount_result = await self.db.execute(
                        select(FeeDiscount).where(FeeDiscount.id == assignment.discount_id, FeeDiscount.is_active == True)
                    )
                    discount = discount_result.scalar_one_or_none()

                base_amount = assignment.custom_amount if assignment.custom_amount is not None else structure.amount
                discount_amount = self._calculate_discount(base_amount, discount)
                net = max(base_amount - discount_amount, 0)
                invoice_total += net

                self.db.add(
                    FeeInvoiceItem(
                        invoice_id=invoice.id,
                        fee_category_id=structure.fee_category_id,
                        amount=base_amount,
                        discount_amt=discount_amount,
                        fine_applied=0,
                    )
                )

            invoice.total_amount = invoice_total
            invoice.balance_amount = invoice_total
            created += 1

        await self.db.flush()
        return created, skipped

    async def list_invoices(
        self,
        school_id: str,
        academic_year_id: str | None = None,
        student_id: str | None = None,
        section_id: str | None = None,
        status: InvoiceStatus | None = None,
        month: int | None = None,
        year: int | None = None,
    ) -> list[FeeInvoice]:
        query = select(FeeInvoice).where(FeeInvoice.school_id == school_id)
        if academic_year_id:
            query = query.where(FeeInvoice.academic_year_id == academic_year_id)
        if student_id:
            query = query.where(FeeInvoice.student_id == student_id)
        if section_id:
            query = query.join(
                StudentEnrollment,
                and_(
                    StudentEnrollment.student_id == FeeInvoice.student_id,
                    StudentEnrollment.section_id == section_id,
                ),
            )
        if status:
            query = query.where(FeeInvoice.status == status)
        if month:
            query = query.where(extract("month", FeeInvoice.invoice_date) == month)
        if year:
            query = query.where(extract("year", FeeInvoice.invoice_date) == year)
        result = await self.db.execute(query.order_by(FeeInvoice.invoice_date.desc(), FeeInvoice.created_at.desc()))
        return list(result.scalars().all())

    async def get_invoice(self, school_id: str, invoice_id: str, for_update: bool = False) -> FeeInvoice | None:
        q = select(FeeInvoice).where(FeeInvoice.school_id == school_id, FeeInvoice.id == invoice_id)
        if for_update:
            # Row-level lock: serialize concurrent payments on the same invoice so two
            # simultaneous collections cannot both read a stale balance and over-credit.
            q = q.with_for_update()
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def get_invoice_items(self, invoice_id: str) -> list[tuple[FeeInvoiceItem, str]]:
        result = await self.db.execute(
            select(FeeInvoiceItem, FeeCategory.name)
            .join(FeeCategory, FeeCategory.id == FeeInvoiceItem.fee_category_id)
            .where(FeeInvoiceItem.invoice_id == invoice_id)
        )
        return list(result.all())

    async def collect_payment(
        self,
        school_id: str,
        invoice_id: str,
        amount: int,
        payment_date: date,
        payment_method,
        collected_by: str,
        transaction_id: str | None,
        remarks: str | None,
    ) -> FeePayment:
        invoice = await self.get_invoice(school_id, invoice_id, for_update=True)
        if not invoice:
            raise ValueError("Invoice not found")
        if invoice.status in [InvoiceStatus.cancelled, InvoiceStatus.waived]:
            raise ValueError("Cannot collect payment for this invoice status")
        if amount > int(invoice.balance_amount):
            raise ValueError("Payment amount exceeds invoice balance")

        receipt_number = f"RCPT-{date.today().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        payment = FeePayment(
            school_id=school_id,
            invoice_id=invoice_id,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            transaction_id=transaction_id,
            receipt_number=receipt_number,
            collected_by=collected_by,
            remarks=remarks,
        )
        self.db.add(payment)

        invoice.paid_amount = int(invoice.paid_amount) + amount
        invoice.balance_amount = int(invoice.total_amount) - int(invoice.paid_amount)
        if invoice.paid_amount <= 0:
            invoice.status = InvoiceStatus.unpaid
        elif invoice.paid_amount < invoice.total_amount:
            invoice.status = InvoiceStatus.partial
        else:
            invoice.status = InvoiceStatus.paid

        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def get_payment(self, school_id: str, payment_id: str) -> FeePayment | None:
        result = await self.db.execute(
            select(FeePayment).where(FeePayment.school_id == school_id, FeePayment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def reverse_payment(self, school_id: str, payment_id: str, reason: str) -> tuple[FeePayment, FeeInvoice]:
        payment = await self.get_payment(school_id, payment_id)
        if not payment:
            raise ValueError("Payment not found")
        if payment.is_reversed:
            raise ValueError("Payment already reversed")

        invoice = await self.get_invoice(school_id, str(payment.invoice_id))
        if not invoice:
            raise ValueError("Invoice not found")

        invoice.paid_amount = max(0, int(invoice.paid_amount) - int(payment.amount))
        invoice.balance_amount = int(invoice.total_amount) - int(invoice.paid_amount)
        if invoice.paid_amount == 0:
            invoice.status = InvoiceStatus.unpaid
        elif invoice.paid_amount < invoice.total_amount:
            invoice.status = InvoiceStatus.partial
        else:
            invoice.status = InvoiceStatus.paid

        payment.is_reversed = True
        payment.reversal_reason = reason
        await self.db.flush()
        return payment, invoice

    async def list_payments(
        self,
        school_id: str,
        from_date: date | None = None,
        to_date: date | None = None,
        invoice_id: str | None = None,
    ) -> list[FeePayment]:
        query = select(FeePayment).where(FeePayment.school_id == school_id)
        if from_date:
            query = query.where(FeePayment.payment_date >= from_date)
        if to_date:
            query = query.where(FeePayment.payment_date <= to_date)
        if invoice_id:
            query = query.where(FeePayment.invoice_id == invoice_id)
        result = await self.db.execute(query.order_by(FeePayment.payment_date.desc(), FeePayment.created_at.desc()))
        return list(result.scalars().all())

    async def get_fine_configuration(self, school_id: str) -> FineConfiguration | None:
        result = await self.db.execute(select(FineConfiguration).where(FineConfiguration.school_id == school_id))
        return result.scalar_one_or_none()

    async def upsert_fine_configuration(self, school_id: str, data: dict) -> FineConfiguration:
        existing = await self.get_fine_configuration(school_id)
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        created = FineConfiguration(school_id=school_id, **data)
        self.db.add(created)
        await self.db.flush()
        await self.db.refresh(created)
        return created

    async def apply_fine(self, school_id: str, as_of_date: date) -> int:
        config = await self.get_fine_configuration(school_id)
        if not config or not config.is_active or float(config.value) <= 0:
            return 0

        result = await self.db.execute(
            select(FeeInvoice)
            .where(
                FeeInvoice.school_id == school_id,
                FeeInvoice.status.in_([InvoiceStatus.unpaid, InvoiceStatus.partial, InvoiceStatus.overdue]),
                FeeInvoice.due_date < as_of_date,
            )
            .order_by(FeeInvoice.due_date.asc())
        )
        invoices = list(result.scalars().all())

        updated = 0
        for invoice in invoices:
            overdue_days = (as_of_date - invoice.due_date).days - int(config.applicable_after_days)
            if overdue_days <= 0:
                continue

            items = await self.get_invoice_items(str(invoice.id))
            existing_fine = sum(int(item.fine_applied) for item, _ in items)
            base_amount = max(int(invoice.total_amount) - existing_fine, 0)

            if config.type == FineCalcType.fixed:
                desired_fine = int(Decimal(config.value))
            else:
                desired_fine = int(round(base_amount * float(config.value) * overdue_days / 100.0))

            if desired_fine <= existing_fine:
                continue

            delta = desired_fine - existing_fine
            invoice.total_amount = int(invoice.total_amount) + delta
            invoice.status = InvoiceStatus.overdue

            if items:
                first_item = items[0][0]
                first_item.fine_applied = int(first_item.fine_applied) + delta

            updated += 1

        await self.db.flush()
        return updated

    async def get_student_statement(self, school_id: str, student_id: str, academic_year_id: str) -> dict:
        student_result = await self.db.execute(
            select(Student.first_name, Student.last_name).where(Student.school_id == school_id, Student.id == student_id)
        )
        student = student_result.first()
        if not student:
            raise ValueError("Student not found")

        invoices = await self.list_invoices(
            school_id=school_id,
            academic_year_id=academic_year_id,
            student_id=student_id,
        )

        total_amount = sum(int(inv.total_amount) for inv in invoices)
        total_paid = sum(int(inv.paid_amount) for inv in invoices)
        total_due = sum(int(inv.balance_amount) for inv in invoices)

        return {
            "student_id": str(student_id),
            "student_name": f"{student[0]} {student[1]}",
            "academic_year_id": str(academic_year_id),
            "total_amount": total_amount,
            "total_paid": total_paid,
            "total_due": total_due,
            "invoices": invoices,
        }

    async def list_defaulters(self, school_id: str, academic_year_id: str, as_of_date: date) -> list[dict]:
        result = await self.db.execute(
            select(
                FeeInvoice.id,
                FeeInvoice.invoice_number,
                FeeInvoice.student_id,
                FeeInvoice.due_date,
                FeeInvoice.balance_amount,
                Student.first_name,
                Student.last_name,
            )
            .join(Student, Student.id == FeeInvoice.student_id)
            .where(
                FeeInvoice.school_id == school_id,
                FeeInvoice.academic_year_id == academic_year_id,
                FeeInvoice.due_date < as_of_date,
                FeeInvoice.balance_amount > 0,
                FeeInvoice.status.in_([InvoiceStatus.unpaid, InvoiceStatus.partial, InvoiceStatus.overdue]),
            )
            .order_by(FeeInvoice.due_date.asc())
        )
        rows = []
        for invoice_id, invoice_number, student_id, due_date, balance_amount, first_name, last_name in result.all():
            rows.append(
                {
                    "student_id": str(student_id),
                    "student_name": f"{first_name} {last_name}",
                    "invoice_id": str(invoice_id),
                    "invoice_number": invoice_number,
                    "due_date": due_date,
                    "balance_amount": int(balance_amount),
                    "days_overdue": (as_of_date - due_date).days,
                }
            )
        return rows

    async def daily_collection_summary(self, school_id: str, day: date) -> dict:
        result = await self.db.execute(
            select(
                FeePayment.payment_method,
                func.sum(FeePayment.amount),
                func.count(FeePayment.id),
            )
            .where(FeePayment.school_id == school_id, FeePayment.payment_date == day)
            .group_by(FeePayment.payment_method)
        )

        by_method: dict[str, int] = {}
        total_collected = 0
        transaction_count = 0
        for method, amount, count in result.all():
            key = getattr(method, "value", str(method))
            by_method[key] = int(amount or 0)
            total_collected += int(amount or 0)
            transaction_count += int(count or 0)

        return {
            "total_collected": total_collected,
            "transaction_count": transaction_count,
            "by_method": by_method,
        }

    async def monthly_collection_summary(
        self,
        school_id: str,
        month: int,
        year: int,
    ) -> dict:
        result = await self.db.execute(
            select(
                FeePayment.payment_method,
                func.sum(FeePayment.amount),
                func.count(FeePayment.id),
            )
            .where(
                FeePayment.school_id == school_id,
                extract("month", FeePayment.payment_date) == month,
                extract("year", FeePayment.payment_date) == year,
            )
            .group_by(FeePayment.payment_method)
        )

        by_method: dict[str, int] = {}
        total_collected = 0
        transaction_count = 0
        for method, amount, count in result.all():
            key = getattr(method, "value", str(method))
            by_method[key] = int(amount or 0)
            total_collected += int(amount or 0)
            transaction_count += int(count or 0)

        return {
            "total_collected": total_collected,
            "transaction_count": transaction_count,
            "by_method": by_method,
        }

    async def get_invoice_party(self, school_id: str, invoice_id: str) -> tuple[str | None, str | None, str | None]:
        result = await self.db.execute(
            select(FeeInvoice.invoice_number, Student.id, Student.first_name, Student.last_name)
            .join(Student, Student.id == FeeInvoice.student_id)
            .where(FeeInvoice.school_id == school_id, FeeInvoice.id == invoice_id)
        )
        row = result.first()
        if not row:
            return None, None, None
        return row[0], str(row[1]), f"{row[2]} {row[3]}"

    async def get_invoice_class_section(self, invoice_id: str, academic_year_id: str) -> tuple[str | None, str | None]:
        """Return (class_name, section_name) for the student's active enrollment."""
        result = await self.db.execute(
            select(Class.name, Section.name)
            .select_from(FeeInvoice)
            .join(StudentEnrollment, StudentEnrollment.student_id == FeeInvoice.student_id)
            .join(Class, Class.id == StudentEnrollment.class_id)
            .outerjoin(Section, Section.id == StudentEnrollment.section_id)
            .where(
                FeeInvoice.id == invoice_id,
                StudentEnrollment.academic_year_id == academic_year_id,
                StudentEnrollment.is_current == True,
            )
        )
        row = result.first()
        if not row:
            return None, None
        return row[0], row[1]

    # ── Student Discount Assignments ─────────────────────────────────────────

    async def list_student_discounts(
        self, school_id: str, student_id: str, academic_year_id: str | None = None
    ) -> list[tuple]:
        query = (
            select(
                StudentDiscountAssignment,
                FeeDiscount.name,
                FeeDiscount.type,
                FeeDiscount.value,
                FeeDiscount.nature,
            )
            .join(FeeDiscount, FeeDiscount.id == StudentDiscountAssignment.discount_id)
            .where(
                StudentDiscountAssignment.school_id == school_id,
                StudentDiscountAssignment.student_id == student_id,
            )
        )
        if academic_year_id:
            query = query.where(StudentDiscountAssignment.academic_year_id == academic_year_id)
        result = await self.db.execute(query.order_by(StudentDiscountAssignment.created_at.desc()))
        return list(result.all())

    async def assign_student_discount(
        self, school_id: str, student_id: str, discount_id: str, academic_year_id: str, remarks: str | None
    ) -> StudentDiscountAssignment:
        row = StudentDiscountAssignment(
            school_id=school_id,
            student_id=student_id,
            discount_id=discount_id,
            academic_year_id=academic_year_id,
            remarks=remarks,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def remove_student_discount(self, school_id: str, assignment_id: str) -> None:
        result = await self.db.execute(
            select(StudentDiscountAssignment).where(
                StudentDiscountAssignment.school_id == school_id,
                StudentDiscountAssignment.id == assignment_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            raise ValueError("Discount assignment not found")
        await self.db.delete(row)
        await self.db.flush()

    # ── Fee Clearance ─────────────────────────────────────────────────────────

    async def check_clearance(
        self, school_id: str, student_id: str, academic_year_id: str
    ) -> dict:
        student_result = await self.db.execute(
            select(Student.first_name, Student.last_name)
            .where(Student.school_id == school_id, Student.id == student_id)
        )
        student = student_result.first()
        if not student:
            raise ValueError("Student not found")

        result = await self.db.execute(
            select(func.count(FeeInvoice.id), func.coalesce(func.sum(FeeInvoice.balance_amount), 0))
            .where(
                FeeInvoice.school_id == school_id,
                FeeInvoice.student_id == student_id,
                FeeInvoice.academic_year_id == academic_year_id,
                FeeInvoice.balance_amount > 0,
                FeeInvoice.status.notin_([InvoiceStatus.cancelled, InvoiceStatus.waived]),
            )
        )
        count, total = result.first()
        return {
            "student_id": str(student_id),
            "student_name": f"{student[0]} {student[1]}",
            "academic_year_id": str(academic_year_id),
            "has_outstanding": int(count) > 0,
            "total_outstanding": int(total),
            "outstanding_invoices": int(count),
        }

    # ── Fee Rollover ──────────────────────────────────────────────────────────

    async def rollover_structures(
        self, school_id: str, from_year_id: str, to_year_id: str
    ) -> tuple[int, int]:
        existing = await self.db.execute(
            select(FeeStructure).where(
                FeeStructure.school_id == school_id,
                FeeStructure.academic_year_id == from_year_id,
                FeeStructure.is_active == True,
            )
        )
        structs = list(existing.scalars().all())
        created = 0
        skipped = 0
        for s in structs:
            check = await self.db.execute(
                select(FeeStructure.id).where(
                    FeeStructure.school_id == school_id,
                    FeeStructure.academic_year_id == to_year_id,
                    FeeStructure.class_id == s.class_id,
                    FeeStructure.fee_category_id == s.fee_category_id,
                )
            )
            if check.scalar_one_or_none():
                skipped += 1
                continue
            new_s = FeeStructure(
                school_id=school_id,
                academic_year_id=to_year_id,
                class_id=s.class_id,
                fee_category_id=s.fee_category_id,
                amount=s.amount,
                frequency=s.frequency,
                due_day=s.due_day,
                is_active=True,
            )
            self.db.add(new_s)
            created += 1
        await self.db.flush()
        return created, skipped

    async def update_overdue_flags(self, school_id: str, as_of_date: date) -> int:
        result = await self.db.execute(
            select(FeeInvoice).where(
                FeeInvoice.school_id == school_id,
                FeeInvoice.status.in_([InvoiceStatus.unpaid, InvoiceStatus.partial]),
                FeeInvoice.due_date < as_of_date,
                FeeInvoice.balance_amount > 0,
            )
        )
        rows = list(result.scalars().all())
        for row in rows:
            row.status = InvoiceStatus.overdue
        await self.db.flush()
        return len(rows)

    async def list_classes_with_outstanding(self, school_id: str, academic_year_id: str) -> list[tuple[str, int]]:
        result = await self.db.execute(
            select(Class.name, func.sum(FeeInvoice.balance_amount))
            .join(StudentEnrollment, StudentEnrollment.student_id == FeeInvoice.student_id)
            .join(Class, Class.id == StudentEnrollment.class_id)
            .where(
                FeeInvoice.school_id == school_id,
                FeeInvoice.academic_year_id == academic_year_id,
                StudentEnrollment.academic_year_id == academic_year_id,
                StudentEnrollment.is_current == True,
            )
            .group_by(Class.name)
            .order_by(Class.name.asc())
        )
        return [(name, int(total or 0)) for name, total in result.all()]

