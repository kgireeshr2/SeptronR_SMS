"""Repository for Advanced Fee Management (v2)."""
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fees import (
    FeeCollectionItem,
    FeeCollection,
    FeeGroup,
    FeeGroupItem,
    FeeMaster,
    FeeMasterItem,
    FeeType,
    StudentFeeMasterAssignment,
)
from app.models.classes import Class
from app.models.students import Student, StudentEnrollment
from app.models.academic import AcademicYear
from app.models.auth import User
from app.schemas.fees_v2 import (
    FeeCollectionCreate,
    FeeGroupCreate,
    FeeGroupUpdate,
    FeeMasterCreate,
    FeeMasterUpdate,
    FeeTypeCreate,
    FeeTypeUpdate,
    StudentFeeMasterAssignRequest,
)


class FeeV2Repository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Fee Types ──────────────────────────────────────────

    async def list_fee_types(self, school_id: str) -> list[FeeType]:
        result = await self.db.execute(
            select(FeeType)
            .where(FeeType.school_id == school_id)
            .order_by(FeeType.name)
        )
        return list(result.scalars().all())

    async def get_fee_type(self, school_id: str, fee_type_id: str) -> Optional[FeeType]:
        result = await self.db.execute(
            select(FeeType).where(FeeType.school_id == school_id, FeeType.id == fee_type_id)
        )
        return result.scalar_one_or_none()

    async def create_fee_type(self, school_id: str, data: FeeTypeCreate) -> FeeType:
        row = FeeType(school_id=school_id, **data.model_dump())
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def update_fee_type(self, row: FeeType, data: FeeTypeUpdate) -> FeeType:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def delete_fee_type(self, row: FeeType) -> None:
        await self.db.delete(row)
        await self.db.flush()

    # ─── Fee Groups ─────────────────────────────────────────

    async def list_fee_groups(self, school_id: str) -> list[dict]:
        groups_result = await self.db.execute(
            select(FeeGroup).where(FeeGroup.school_id == school_id).order_by(FeeGroup.name)
        )
        groups = list(groups_result.scalars().all())
        out = []
        for g in groups:
            items_result = await self.db.execute(
                select(FeeType)
                .join(FeeGroupItem, FeeGroupItem.fee_type_id == FeeType.id)
                .where(FeeGroupItem.fee_group_id == str(g.id))
            )
            fee_types = list(items_result.scalars().all())
            out.append({"group": g, "fee_types": fee_types})
        return out

    async def get_fee_group(self, school_id: str, group_id: str) -> Optional[FeeGroup]:
        result = await self.db.execute(
            select(FeeGroup).where(FeeGroup.school_id == school_id, FeeGroup.id == group_id)
        )
        return result.scalar_one_or_none()

    async def get_fee_group_types(self, group_id: str) -> list[FeeType]:
        result = await self.db.execute(
            select(FeeType)
            .join(FeeGroupItem, FeeGroupItem.fee_type_id == FeeType.id)
            .where(FeeGroupItem.fee_group_id == group_id)
        )
        return list(result.scalars().all())

    async def create_fee_group(self, school_id: str, data: FeeGroupCreate) -> FeeGroup:
        row = FeeGroup(
            school_id=school_id,
            name=data.name,
            description=data.description,
            is_active=data.is_active,
        )
        self.db.add(row)
        await self.db.flush()
        for type_id in data.fee_type_ids:
            self.db.add(FeeGroupItem(fee_group_id=str(row.id), fee_type_id=type_id))
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def update_fee_group(self, row: FeeGroup, data: FeeGroupUpdate) -> FeeGroup:
        update_data = data.model_dump(exclude_unset=True)
        fee_type_ids = update_data.pop("fee_type_ids", None)
        for key, value in update_data.items():
            setattr(row, key, value)
        if fee_type_ids is not None:
            # Rebuild items
            existing = await self.db.execute(
                select(FeeGroupItem).where(FeeGroupItem.fee_group_id == str(row.id))
            )
            for item in existing.scalars().all():
                await self.db.delete(item)
            await self.db.flush()
            for type_id in fee_type_ids:
                self.db.add(FeeGroupItem(fee_group_id=str(row.id), fee_type_id=type_id))
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def delete_fee_group(self, row: FeeGroup) -> None:
        await self.db.delete(row)
        await self.db.flush()

    # ─── Fee Masters ────────────────────────────────────────

    async def list_fee_masters(
        self, school_id: str, class_id: Optional[str] = None, year_id: Optional[str] = None
    ) -> list[dict]:
        query = (
            select(FeeMaster, Class.name, AcademicYear.name, FeeGroup.name)
            .join(Class, Class.id == FeeMaster.class_id)
            .join(AcademicYear, AcademicYear.id == FeeMaster.academic_year_id)
            .join(FeeGroup, FeeGroup.id == FeeMaster.fee_group_id)
            .where(FeeMaster.school_id == school_id)
            .order_by(FeeMaster.name)
        )
        if class_id:
            query = query.where(FeeMaster.class_id == class_id)
        if year_id:
            query = query.where(FeeMaster.academic_year_id == year_id)
        rows = await self.db.execute(query)
        out = []
        for master, cls_name, yr_name, grp_name in rows.all():
            items = await self._get_master_items(str(master.id))
            out.append({
                "master": master,
                "class_name": cls_name,
                "academic_year_name": yr_name,
                "fee_group_name": grp_name,
                "items": items,
            })
        return out

    async def _get_master_items(self, master_id: str) -> list[dict]:
        result = await self.db.execute(
            select(FeeMasterItem, FeeType.name)
            .join(FeeType, FeeType.id == FeeMasterItem.fee_type_id)
            .where(FeeMasterItem.fee_master_id == master_id)
        )
        return [{"item": row[0], "fee_type_name": row[1]} for row in result.all()]

    async def get_fee_master(self, school_id: str, master_id: str) -> Optional[FeeMaster]:
        result = await self.db.execute(
            select(FeeMaster).where(FeeMaster.school_id == school_id, FeeMaster.id == master_id)
        )
        return result.scalar_one_or_none()

    async def create_fee_master(self, school_id: str, data: FeeMasterCreate) -> FeeMaster:
        row = FeeMaster(
            school_id=school_id,
            name=data.name,
            class_id=data.class_id,
            academic_year_id=data.academic_year_id,
            fee_group_id=data.fee_group_id,
            is_active=data.is_active,
        )
        self.db.add(row)
        await self.db.flush()
        for item in data.items:
            self.db.add(FeeMasterItem(
                fee_master_id=str(row.id),
                fee_type_id=item.fee_type_id,
                amount=item.amount,
            ))
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def update_fee_master(self, row: FeeMaster, data: FeeMasterUpdate) -> FeeMaster:
        update_data = data.model_dump(exclude_unset=True)
        items = update_data.pop("items", None)
        for key, value in update_data.items():
            setattr(row, key, value)
        if items is not None:
            existing = await self.db.execute(
                select(FeeMasterItem).where(FeeMasterItem.fee_master_id == str(row.id))
            )
            for item in existing.scalars().all():
                await self.db.delete(item)
            await self.db.flush()
            for item in items:
                self.db.add(FeeMasterItem(
                    fee_master_id=str(row.id),
                    fee_type_id=item["fee_type_id"],
                    amount=item["amount"],
                ))
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def delete_fee_master(self, row: FeeMaster) -> None:
        await self.db.delete(row)
        await self.db.flush()

    # ─── Student Assignments ─────────────────────────────────

    async def list_assignments(
        self, school_id: str, year_id: Optional[str] = None, class_id: Optional[str] = None
    ) -> list[dict]:
        query = (
            select(StudentFeeMasterAssignment, Student.first_name, Student.last_name, FeeMaster.name)
            .join(Student, Student.id == StudentFeeMasterAssignment.student_id)
            .join(FeeMaster, FeeMaster.id == StudentFeeMasterAssignment.fee_master_id)
            .where(StudentFeeMasterAssignment.school_id == school_id)
            .order_by(Student.first_name)
        )
        if year_id:
            query = query.where(StudentFeeMasterAssignment.academic_year_id == year_id)
        if class_id:
            query = query.where(FeeMaster.class_id == class_id)
        rows = await self.db.execute(query)
        return [
            {
                "assignment": row[0],
                "student_name": f"{row[1]} {row[2]}",
                "fee_master_name": row[3],
            }
            for row in rows.all()
        ]

    async def get_assignment(self, school_id: str, assignment_id: str) -> Optional[StudentFeeMasterAssignment]:
        result = await self.db.execute(
            select(StudentFeeMasterAssignment).where(
                StudentFeeMasterAssignment.school_id == school_id,
                StudentFeeMasterAssignment.id == assignment_id,
            )
        )
        return result.scalar_one_or_none()

    async def assign_fee_master(
        self, school_id: str, data: StudentFeeMasterAssignRequest, assigned_by: str
    ) -> list[StudentFeeMasterAssignment]:
        created = []
        for student_id in data.student_ids:
            # Check existing
            existing = await self.db.execute(
                select(StudentFeeMasterAssignment).where(
                    StudentFeeMasterAssignment.student_id == student_id,
                    StudentFeeMasterAssignment.fee_master_id == data.fee_master_id,
                    StudentFeeMasterAssignment.academic_year_id == data.academic_year_id,
                )
            )
            if existing.scalar_one_or_none():
                continue
            row = StudentFeeMasterAssignment(
                school_id=school_id,
                student_id=student_id,
                fee_master_id=data.fee_master_id,
                academic_year_id=data.academic_year_id,
                assigned_by=assigned_by,
            )
            self.db.add(row)
            created.append(row)
        await self.db.flush()
        return created

    async def remove_assignment(self, row: StudentFeeMasterAssignment) -> None:
        await self.db.delete(row)
        await self.db.flush()

    # ─── Fee Ledger (per student summary) ────────────────────

    async def get_student_ledger(
        self, school_id: str, student_id: str, year_id: str
    ) -> list[dict]:
        """Return fee types due, paid and balance for a student in a given year.
        Returns a list — one entry per fee master assignment (students may have
        multiple fee masters assigned, e.g. tuition + transport + hostel).
        """
        assign_result = await self.db.execute(
            select(StudentFeeMasterAssignment, FeeMaster.name)
            .join(FeeMaster, FeeMaster.id == StudentFeeMasterAssignment.fee_master_id)
            .where(
                StudentFeeMasterAssignment.school_id == school_id,
                StudentFeeMasterAssignment.student_id == student_id,
                StudentFeeMasterAssignment.academic_year_id == year_id,
            )
            .order_by(FeeMaster.name)
        )
        rows = assign_result.all()
        if not rows:
            return []

        student = await self.db.get(Student, student_id)
        student_name = f"{student.first_name} {student.last_name}" if student else "Unknown"

        ledgers: list[dict] = []
        for assignment, master_name in rows:
            items = await self._get_master_items(str(assignment.fee_master_id))

            # Aggregate paid vs discount per fee type (only non-reversed)
            paid_result = await self.db.execute(
                select(
                    FeeCollectionItem.fee_type_id,
                    func.sum(FeeCollectionItem.amount_paid).label("paid"),
                    func.sum(FeeCollectionItem.discount_amount).label("discount"),
                )
                .join(FeeCollection, FeeCollection.id == FeeCollectionItem.collection_id)
                .where(
                    FeeCollection.school_id == school_id,
                    FeeCollection.student_id == student_id,
                    FeeCollection.fee_master_id == str(assignment.fee_master_id),
                    FeeCollection.academic_year_id == year_id,
                    FeeCollection.is_reversed == False,  # noqa: E712
                )
                .group_by(FeeCollectionItem.fee_type_id)
            )
            paid_map = {str(r.fee_type_id): (r.paid or 0, r.discount or 0) for r in paid_result.all()}

            entries = []
            total_due = total_paid = total_discount = 0
            for item_dict in items:
                item = item_dict["item"]
                type_name = item_dict["fee_type_name"]
                key = str(item.fee_type_id)
                paid, discount = paid_map.get(key, (0, 0))
                balance = item.amount - paid - discount
                entries.append({
                    "fee_type_id": key,
                    "fee_type_name": type_name,
                    "amount_due": item.amount,
                    "amount_paid": paid,
                    "discount_given": discount,
                    "balance": balance,
                })
                total_due += item.amount
                total_paid += paid
                total_discount += discount

            ledgers.append({
                "student_id": str(student_id),
                "student_name": student_name,
                "fee_master_id": str(assignment.fee_master_id),
                "fee_master_name": master_name,
                "total_due": total_due,
                "total_paid": total_paid,
                "total_discount": total_discount,
                "total_balance": total_due - total_paid - total_discount,
                "entries": entries,
            })

        return ledgers

    # ─── Fee Collection ──────────────────────────────────────

    async def list_collections(
        self,
        school_id: str,
        student_id: Optional[str] = None,
        year_id: Optional[str] = None,
        include_reversed: bool = False,
    ) -> list[dict]:
        query = (
            select(
                FeeCollection,
                Student.first_name,
                Student.last_name,
                FeeMaster.name,
                User.username,
            )
            .join(Student, Student.id == FeeCollection.student_id)
            .join(FeeMaster, FeeMaster.id == FeeCollection.fee_master_id)
            .join(User, User.id == FeeCollection.collected_by)
            .where(FeeCollection.school_id == school_id)
            .order_by(FeeCollection.payment_date.desc(), FeeCollection.created_at.desc())
        )
        if student_id:
            query = query.where(FeeCollection.student_id == student_id)
        if year_id:
            query = query.where(FeeCollection.academic_year_id == year_id)
        if not include_reversed:
            query = query.where(FeeCollection.is_reversed == False)  # noqa: E712

        rows = await self.db.execute(query)
        out = []
        for coll, first_name, last_name, master_name, username in rows.all():
            items = await self._get_collection_items(str(coll.id))
            out.append({
                "collection": coll,
                "student_name": f"{first_name} {last_name}",
                "fee_master_name": master_name,
                "collected_by_name": username,
                "items": items,
            })
        return out

    async def _get_collection_items(self, collection_id: str) -> list[dict]:
        result = await self.db.execute(
            select(FeeCollectionItem, FeeType.name)
            .join(FeeType, FeeType.id == FeeCollectionItem.fee_type_id)
            .where(FeeCollectionItem.collection_id == collection_id)
        )
        return [{"item": row[0], "fee_type_name": row[1]} for row in result.all()]

    async def get_collection(self, school_id: str, collection_id: str) -> Optional[FeeCollection]:
        result = await self.db.execute(
            select(FeeCollection).where(
                FeeCollection.school_id == school_id,
                FeeCollection.id == collection_id,
            )
        )
        return result.scalar_one_or_none()

    def _generate_receipt(self, school_id: str) -> str:
        ts = datetime.now(timezone.utc)
        uid = str(uuid4()).split("-")[0].upper()
        return f"RCV-{ts.strftime('%Y%m%d')}-{uid}"

    async def collect_fee(
        self, school_id: str, data: FeeCollectionCreate, collected_by: str
    ) -> FeeCollection:
        total_amount = sum(i.amount_paid for i in data.items)
        total_discount = sum(i.discount_amount for i in data.items)

        coll = FeeCollection(
            school_id=school_id,
            student_id=data.student_id,
            fee_master_id=data.fee_master_id,
            academic_year_id=data.academic_year_id,
            receipt_number=self._generate_receipt(school_id),
            payment_date=data.payment_date,
            total_amount=total_amount,
            total_discount=total_discount,
            payment_method=data.payment_method,
            transaction_ref=data.transaction_ref,
            collected_by=collected_by,
            remarks=data.remarks,
            is_reversed=False,
        )
        self.db.add(coll)
        await self.db.flush()

        for item in data.items:
            self.db.add(FeeCollectionItem(
                collection_id=str(coll.id),
                fee_type_id=item.fee_type_id,
                amount_paid=item.amount_paid,
                discount_amount=item.discount_amount,
                discount_reason=item.discount_reason,
            ))
        await self.db.flush()
        await self.db.refresh(coll)
        return coll

    async def reverse_collection(
        self, row: FeeCollection, reason: str, reversed_by: str
    ) -> FeeCollection:
        row.is_reversed = True
        row.reversal_reason = reason
        row.reversed_by = reversed_by
        row.reversed_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(row)
        return row
