from typing import Optional
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rbac import Role, Permission, RolePermission


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_school(self, school_id: Optional[str]) -> list[Role]:
        """List roles for a school. When school_id is provided, return only school-specific
        roles. When school_id is None (super-admin context), return global roles."""
        if school_id:
            stmt = select(Role).where(
                Role.school_id == school_id
            ).order_by(Role.is_system.desc(), Role.name)
        else:
            stmt = select(Role).where(
                Role.school_id.is_(None)
            ).order_by(Role.is_system.desc(), Role.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, role_id: str, school_id: Optional[str] = None) -> Optional[Role]:
        """Fetch a role by id. When school_id is provided the role must belong to
        that school (cross-school access returns None). When omitted (internal/
        super-admin global context) the lookup is unscoped."""
        stmt = select(Role).where(Role.id == role_id)
        if school_id is not None:
            stmt = stmt.where(Role.school_id == school_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str, school_id: Optional[str] = None) -> Optional[Role]:
        stmt = select(Role).where(Role.slug == slug, Role.school_id == school_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, school_id: Optional[str], data: dict) -> Role:
        role = Role(school_id=school_id, **data)
        self.db.add(role)
        await self.db.flush()
        await self.db.refresh(role)
        return role

    async def update(self, role_id: str, data: dict) -> Optional[Role]:
        await self.db.execute(update(Role).where(Role.id == role_id).values(**data))
        await self.db.flush()
        return await self.get_by_id(role_id)

    async def delete(self, role_id: str) -> None:
        await self.db.execute(delete(Role).where(Role.id == role_id))
        await self.db.flush()

    async def assign_permissions(self, role_id: str, permission_ids: list[str]) -> None:
        """Replace the full permission set for a role."""
        # Remove existing
        await self.db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        # Add new
        for perm_id in permission_ids:
            self.db.add(RolePermission(role_id=role_id, permission_id=perm_id))
        await self.db.flush()

    async def get_permissions(self, role_id: str) -> list[Permission]:
        stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
            .order_by(Permission.module, Permission.action)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def clone_role(self, role_id: str, new_name: str, school_id: str) -> Role:
        """Clone a role with a new name for the given school."""
        import re
        original = await self.get_by_id(role_id)
        if not original:
            raise ValueError("Role not found")
        # Only allow cloning a global/system template or a role owned by this school —
        # never another school's role.
        if original.school_id is not None and str(original.school_id) != str(school_id):
            raise ValueError("Role not found")
        original_perms = await self.get_permissions(role_id)
        new_slug = re.sub(r"[^a-z0-9]+", "_", new_name.lower()).strip("_")
        new_role = Role(
            school_id=school_id,
            name=new_name,
            slug=new_slug,
            description=original.description,
            is_system=False,
            is_active=True,
        )
        self.db.add(new_role)
        await self.db.flush()
        await self.db.refresh(new_role)
        # Clone permissions
        for perm in original_perms:
            self.db.add(RolePermission(role_id=new_role.id, permission_id=perm.id))
        await self.db.flush()
        return new_role

    async def list_all_permissions(self) -> list[Permission]:
        result = await self.db.execute(
            select(Permission).order_by(Permission.module, Permission.action)
        )
        return list(result.scalars().all())

    async def create_permission(self, module: str, action: str, description: str | None = None) -> Permission:
        # Return existing if already present
        existing = await self.db.execute(
            select(Permission).where(Permission.module == module, Permission.action == action)
        )
        perm = existing.scalar_one_or_none()
        if perm:
            return perm
        perm = Permission(module=module, action=action, description=description)
        self.db.add(perm)
        await self.db.commit()
        await self.db.refresh(perm)
        return perm

    async def get_permission_by_id(self, permission_id: str) -> Optional[Permission]:
        result = await self.db.execute(select(Permission).where(Permission.id == permission_id))
        return result.scalar_one_or_none()

