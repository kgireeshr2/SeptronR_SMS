from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, permission_required
from app.db.session import get_db
from app.repositories.role_repository import RoleRepository
from app.schemas.rbac import (
    AssignPermissionsRequest,
    CloneRoleRequest,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from app.utils.response import ok

router = APIRouter(prefix="/roles", tags=["Roles & Permissions"])


def _role_to_response(role, permission_strings: list[str] | None = None) -> dict:
    return RoleResponse(
        id=role.id,
        school_id=role.school_id,
        name=role.name,
        slug=role.slug,
        description=role.description,
        is_system=role.is_system,
        is_active=role.is_active,
        permissions=permission_strings or [],
    ).model_dump()


@router.get("", response_model=dict)
async def list_roles(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("roles", "view")),
):
    """List all roles for the current school."""
    school_id = getattr(request.state, "school_id", None)
    repo = RoleRepository(db)
    roles = await repo.list_by_school(school_id)
    result = []
    for role in roles:
        perms = await repo.get_permissions(str(role.id))
        perm_strings = [f"{p.module}:{p.action}" for p in perms]
        result.append(_role_to_response(role, perm_strings))
    return ok(result, f"{len(result)} roles found")


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("roles", "create")),
):
    """Create a new role for the school."""
    school_id = getattr(request.state, "school_id", None)
    repo = RoleRepository(db)
    # Check slug uniqueness
    existing = await repo.get_by_slug(data.slug, school_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Role slug '{data.slug}' already exists")
    role = await repo.create(school_id, data.model_dump())
    await db.commit()
    return ok(_role_to_response(role), "Role created successfully")


@router.get("/{role_id}", response_model=dict)
async def get_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("roles", "view")),
):
    """Get a role with its permissions."""
    repo = RoleRepository(db)
    role = await repo.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    perms = await repo.get_permissions(role_id)
    perm_strings = [f"{p.module}:{p.action}" for p in perms]
    return ok(_role_to_response(role, perm_strings))


@router.put("/{role_id}", response_model=dict)
async def update_role(
    role_id: str,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("roles", "update")),
):
    """Update a role."""
    repo = RoleRepository(db)
    role = await repo.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    role = await repo.update(role_id, update_data)
    await db.commit()
    perms = await repo.get_permissions(role_id)
    perm_strings = [f"{p.module}:{p.action}" for p in perms]
    return ok(_role_to_response(role, perm_strings), "Role updated successfully")


@router.delete("/{role_id}", response_model=dict)
async def delete_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("roles", "delete")),
):
    """Delete a role (blocked for system roles)."""
    repo = RoleRepository(db)
    role = await repo.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete a system role")
    await repo.delete(role_id)
    await db.commit()
    return ok(None, "Role deleted successfully")


@router.get("/{role_id}/permissions", response_model=dict)
async def get_role_permissions(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("roles", "view")),
):
    """List permissions assigned to a role."""
    repo = RoleRepository(db)
    role = await repo.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    perms = await repo.get_permissions(role_id)
    result = [PermissionResponse.model_validate(p).model_dump() for p in perms]
    return ok(result)


@router.post("/{role_id}/permissions", response_model=dict)
async def assign_permissions(
    role_id: str,
    data: AssignPermissionsRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("roles", "manage")),
):
    """Replace the permission set for a role."""
    repo = RoleRepository(db)
    role = await repo.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    perm_ids = [str(pid) for pid in data.permission_ids]
    await repo.assign_permissions(role_id, perm_ids)
    await db.commit()
    perms = await repo.get_permissions(role_id)
    result = [PermissionResponse.model_validate(p).model_dump() for p in perms]
    return ok(result, "Permissions updated successfully")


@router.post("/{role_id}/clone", response_model=dict, status_code=status.HTTP_201_CREATED)
async def clone_role(
    role_id: str,
    data: CloneRoleRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("roles", "create")),
):
    """Clone a role with a new name."""
    school_id = getattr(request.state, "school_id", None)
    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")
    repo = RoleRepository(db)
    new_role = await repo.clone_role(role_id, data.name, school_id)
    await db.commit()
    perms = await repo.get_permissions(str(new_role.id))
    perm_strings = [f"{p.module}:{p.action}" for p in perms]
    return ok(_role_to_response(new_role, perm_strings), "Role cloned successfully")


# ── Permissions registry ─────────────────────────────────────────────────────

permissions_router = APIRouter(prefix="/permissions", tags=["Roles & Permissions"])


@permissions_router.get("", response_model=dict)
async def list_all_permissions(
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("roles", "view")),
):
    """Get the full platform permission registry."""
    repo = RoleRepository(db)
    perms = await repo.list_all_permissions()
    result = [PermissionResponse.model_validate(p).model_dump() for p in perms]
    return ok(result, f"{len(result)} permissions found")

