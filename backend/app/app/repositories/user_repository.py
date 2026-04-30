from typing import Optional
from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth import User
from app.models.rbac import Permission, UserRole, RolePermission


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, school_id: Optional[str], email: str) -> Optional[User]:
        if school_id:
            stmt = select(User).where(
                and_(User.school_id == school_id, User.email == email, User.deleted_at.is_(None))
            )
        else:
            # When school_id is None, only return super-admin users (school_id IS NULL AND is_super_admin)
            stmt = select(User).where(
                and_(User.school_id.is_(None), User.email == email, User.deleted_at.is_(None), User.is_super_admin == True)
            )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, school_id: Optional[str], username: str) -> Optional[User]:
        if school_id:
            stmt = select(User).where(
                and_(
                    User.school_id == school_id,
                    User.username == username,
                    User.deleted_at.is_(None),
                )
            )
        else:
            # When school_id is None, only return super-admin users
            stmt = select(User).where(
                and_(
                    User.school_id.is_(None),
                    User.username == username,
                    User.deleted_at.is_(None),
                    User.is_super_admin == True,
                )
            )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_phone(self, school_id: Optional[str], phone: str) -> Optional[User]:
        if school_id:
            stmt = select(User).where(
                and_(User.school_id == school_id, User.phone == phone, User.deleted_at.is_(None))
            )
        else:
            # When school_id is None, only return super-admin users
            stmt = select(User).where(
                and_(User.school_id.is_(None), User.phone == phone, User.deleted_at.is_(None), User.is_super_admin == True)
            )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_identifier(self, identifier: str, school_id: Optional[str]) -> Optional[User]:
        """Find user by email OR username OR phone.
        
        If school_id is not provided (None), first tries super-admin scope,
        then falls back to a global search so school users can login without
        needing to specify X-School-Id header.
        """
        # Try within specified scope (school or super-admin)
        user = await self.get_by_email(school_id, identifier)
        if user:
            return user
        user = await self.get_by_username(school_id, identifier)
        if user:
            return user
        user = await self.get_by_phone(school_id, identifier)
        if user:
            return user

        # If no school_id was specified, do a global fallback search
        # This allows school users to login without X-School-Id header
        # Only return active users with a school_id, ordered by newest first
        if school_id is None:
            stmt = (
                select(User).where(
                    and_(
                        User.school_id.isnot(None),
                        User.deleted_at.is_(None),
                        User.is_active == True,
                        (User.email == identifier) | (User.username == identifier) | (User.phone == identifier),
                    )
                )
                .order_by(User.created_at.desc())  # prefer the newest user
                .limit(1)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

        return None

    async def create(self, data: dict) -> User:
        user = User(**data)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: str, data: dict) -> Optional[User]:
        await self.db.execute(
            update(User).where(User.id == user_id).values(**data)
        )
        await self.db.flush()
        return await self.get_by_id(user_id)

    async def get_user_permissions(self, user_id: str) -> set[str]:
        """Returns set of 'module:action' strings via JOIN user_roles → role_permissions → permissions."""
        stmt = (
            select(Permission.module, Permission.action)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
            .distinct()
        )
        result = await self.db.execute(stmt)
        return {f"{row.module}:{row.action}" for row in result.all()}

    async def update_last_login(self, user_id: str) -> None:
        from datetime import datetime, timezone
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.now(timezone.utc))
        )
        await self.db.flush()

    async def assign_roles(self, user_id: str, role_ids: list[str], assigned_by: Optional[str] = None) -> None:
        """Replace all roles for a user."""
        from app.models.rbac import UserRole
        from datetime import datetime, timezone

        # Remove existing roles
        await self.db.execute(
            __import__("sqlalchemy", fromlist=["delete"]).delete(UserRole).where(UserRole.user_id == user_id)
        )
        # Add new roles
        for role_id in role_ids:
            self.db.add(
                UserRole(
                    user_id=user_id,
                    role_id=role_id,
                    assigned_by=assigned_by,
                    assigned_at=datetime.now(timezone.utc),
                )
            )
        await self.db.flush()

    async def list_by_school(
        self,
        school_id: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[dict] = None,
    ) -> tuple[list[User], int]:
        base_stmt = select(User).where(
            and_(User.school_id == school_id, User.deleted_at.is_(None))
        )
        if filters:
            if filters.get("is_active") is not None:
                base_stmt = base_stmt.where(User.is_active == filters["is_active"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                base_stmt = base_stmt.where(
                    User.username.ilike(search) | User.email.ilike(search)
                )
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = base_stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

