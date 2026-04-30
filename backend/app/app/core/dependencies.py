"""
FastAPI dependencies: get_current_user, permission_required, get_school_id.
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=True)

# Module-level Redis client (shared across requests)
redis_client: aioredis.Redis | None = (
    aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    if settings.REDIS_ENABLED
    else None
)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Decode JWT, check blacklist, load user with permissions."""
    from app.repositories.user_repository import UserRepository

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        if not user_id or not jti:
            raise credentials_exception
        # Check blacklist (if Redis enabled)
        if redis_client and await redis_client.get(f"blacklist:jti:{jti}"):
            raise credentials_exception
    except Exception:
        raise credentials_exception

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise credentials_exception

    # Set school context on request state
    header_school_id = request.headers.get("X-School-Id")
    if user.is_super_admin and header_school_id:
        request.state.school_id = header_school_id
    else:
        request.state.school_id = str(user.school_id) if user.school_id else None
    request.state.current_user = user
    return user


def permission_required(module: str, action: str):
    """FastAPI dependency factory for permission checking.

    Permission hierarchy:
    - Exact match: user has `module:action`
    - module:manage grants any action on that module
    - Requesting `module:manage` is granted if user has any write-level perm
    - Legacy action aliases:
        `read` → view
        `write` → create or update or edit
        `edit` → update
    - Module name aliases (code uses plural/alternate, DB stores canonical):
        `communications` → `communication`
        `audit` → `audit_logs`
    """
    # Actions that together imply "manage" level access
    _MANAGE_IMPLIES = {"create", "update", "delete", "manage", "approve", "edit"}

    # Legacy action aliases map to canonical equivalents
    _ACTION_ALIASES: dict[str, list[str]] = {
        "read":  ["view"],
        "write": ["create", "update", "edit"],
        "edit":  ["update"],
    }

    # Module name aliases (endpoint code → DB permission module name)
    _MODULE_ALIASES: dict[str, list[str]] = {
        "communications": ["communication"],
        "audit":          ["audit_logs"],
    }

    async def _check(
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        if current_user.is_super_admin:
            return current_user
        from app.repositories.user_repository import UserRepository
        repo = UserRepository(db)
        permissions = await repo.get_user_permissions(str(current_user.id))

        # Build list of module names to check (original + aliases)
        modules_to_check = [module] + _MODULE_ALIASES.get(module, [])

        for mod in modules_to_check:
            perm_key = f"{mod}:{action}"

            # 1. Exact permission match
            if perm_key in permissions:
                return current_user

            # 2. module:manage grants all actions on the module
            if f"{mod}:manage" in permissions:
                return current_user

            # 3. Requesting :manage — allow if user has any write-level perm for the module
            if action == "manage":
                for implied_action in _MANAGE_IMPLIES:
                    if f"{mod}:{implied_action}" in permissions:
                        return current_user

            # 4. Alias resolution (read→view, write→create/update/edit, edit→update)
            for canonical in _ACTION_ALIASES.get(action, []):
                if f"{mod}:{canonical}" in permissions:
                    return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {module}:{action}",
        )

    return _check


async def get_school_id(request: Request, current_user=Depends(get_current_user)) -> UUID:
    """Extract school_id from request state, headers, or query params.
    
    Depends on get_current_user to ensure request.state.school_id is set
    from the JWT token school_id before this runs.
    """
    school_id = (
        getattr(request.state, "school_id", None)
        or request.headers.get("X-School-Id")
        or request.query_params.get("school_id")
    )
    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School context not found. Provide X-School-Id header.",
        )
    try:
        return UUID(str(school_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid school_id format: {school_id}",
        )
