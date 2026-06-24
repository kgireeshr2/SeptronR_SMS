from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PermissionResponse(BaseModel):
    id: UUID
    module: str
    action: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RoleCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RoleResponse(BaseModel):
    id: UUID
    school_id: Optional[UUID] = None
    name: str
    slug: str
    description: Optional[str] = None
    is_system: bool
    is_active: bool
    permissions: list[str] = []  # ["students:view", ...]

    model_config = ConfigDict(from_attributes=True)


class AssignPermissionsRequest(BaseModel):
    permission_ids: list[UUID]


class AssignRolesRequest(BaseModel):
    role_ids: list[UUID]


class CloneRoleRequest(BaseModel):
    name: str
