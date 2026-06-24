from collections import defaultdict
import re

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, permission_required
from app.db.session import get_db
from app.repositories.school_repository import SchoolProfileRepository, SchoolRepository, SchoolSettingsRepository
from app.schemas.phase3 import BulkSettingsUpdate, SchoolBootstrapCreate, SchoolProfileUpdate, SettingUpdate
from app.services.school_service import seed_school_defaults
from app.utils.file_upload import ALLOWED_IMAGE_TYPES, save_upload_file
from app.utils.response import ok

router = APIRouter(prefix="/schools", tags=["Schools"])


def _slugify_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:90] if slug else "school"


def _school_id_from_request(request: Request, current_user=None) -> str:
    """Extract school_id from request state (set by get_current_user) or headers."""
    # First check if already set in request state by get_current_user
    school_id = getattr(request.state, "school_id", None)
    
    if not school_id:
        # Check headers/query params
        school_id = request.headers.get("X-School-Id") or request.query_params.get("school_id")
    
    if not school_id and current_user:
        # SuperAdmin must provide X-School-Id header to specify which school to manage
        if hasattr(current_user, 'is_super_admin') and current_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SuperAdmin must provide X-School-Id header to specify which school to manage."
            )
        
        # Regular users: use their assigned school_id
        if hasattr(current_user, 'school_id') and current_user.school_id:
            school_id = str(current_user.school_id)
    
    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School context not found. Please provide X-School-Id header."
        )
    return str(school_id)


@router.post("/bootstrap", response_model=dict, status_code=status.HTTP_201_CREATED)
async def bootstrap_school(
    data: SchoolBootstrapCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not getattr(current_user, "is_super_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperAdmin can create schools via bootstrap.",
        )

    school_repo = SchoolRepository(db)
    base_slug = _slugify_name(data.school_name)
    slug = base_slug
    suffix = 1
    while await school_repo.get_by_slug(slug):
        suffix += 1
        slug = f"{base_slug}-{suffix}"

    school = await school_repo.create(
        {
            "name": data.school_name,
            "slug": slug,
            "email": data.email,
            "phone": data.phone,
            "address": data.address,
            "city": data.city,
            "state": data.state,
            "country": data.country or "India",
            "pincode": data.pincode,
            "website": data.website,
            "is_active": True,
        }
    )

    await SchoolProfileRepository(db).upsert(
        str(school.id),
        {
            "school_name": data.school_name,
            "phone": data.phone,
            "email": data.email,
            "website": data.website,
            "address": data.address,
            "city": data.city,
            "state": data.state,
            "country": data.country or "India",
            "pincode": data.pincode,
        },
    )

    await seed_school_defaults(str(school.id), db)

    # Optionally create a school admin user
    admin_user_info = None
    if data.admin_email and data.admin_password:
        from sqlalchemy import select as sa_select
        from app.models.auth import User
        from app.models.rbac import Role, UserRole
        from app.core.security import get_password_hash
        import uuid as _uuid

        # Check if email already exists
        existing_user = (await db.execute(
            sa_select(User).where(User.email == data.admin_email)
        )).scalar_one_or_none()

        if not existing_user:
            admin_user = User(
                school_id=school.id,
                username=data.admin_email.split("@")[0],
                email=data.admin_email,
                phone=data.admin_phone,
                password_hash=get_password_hash(data.admin_password),
                first_name=data.admin_first_name or "School",
                last_name=data.admin_last_name or "Admin",
                is_active=True,
                is_verified=True,
                is_super_admin=False,
            )
            db.add(admin_user)
            await db.flush()

            # Assign school_admin role
            admin_role = (await db.execute(
                sa_select(Role).where(
                    Role.slug == "school_admin",
                    Role.school_id == school.id,
                )
            )).scalar_one_or_none()
            if admin_role:
                db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))

            await db.commit()
            admin_user_info = {
                "email": str(admin_user.email),
                "username": str(admin_user.username),
                "password": data.admin_password,
            }
        else:
            admin_user_info = {"email": data.admin_email, "note": "user already existed"}

    return ok(
        {
            "id": str(school.id),
            "name": school.name,
            "slug": school.slug,
            "admin": admin_user_info,
        },
        "School created successfully",
    )


@router.get("/profile", response_model=dict)
async def get_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    school_id = _school_id_from_request(request, current_user)
    profile = await SchoolProfileRepository(db).get_by_school(school_id)
    return ok(profile, "School profile")


@router.put("/profile", response_model=dict, dependencies=[Depends(permission_required("settings", "update"))])
async def update_profile(
    data: SchoolProfileUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    school_id = _school_id_from_request(request, current_user)
    profile = await SchoolProfileRepository(db).upsert(school_id, data.model_dump(exclude_none=True))
    return ok(profile, "School profile updated")


@router.post("/profile/logo", response_model=dict, dependencies=[Depends(permission_required("settings", "update"))])
async def upload_logo(
    file: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    school_id = _school_id_from_request(request, current_user)
    saved_path = await save_upload_file(file, folder=f"{school_id}/school", allowed_types=ALLOWED_IMAGE_TYPES)
    profile = await SchoolProfileRepository(db).upsert(school_id, {"logo_url": saved_path})
    return ok(profile, "Logo uploaded")


@router.get("/settings", response_model=dict)
async def get_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    school_id = _school_id_from_request(request, current_user)
    rows = await SchoolSettingsRepository(db).get_all(school_id)
    grouped = defaultdict(dict)
    for row in rows:
        grouped[row.category][row.key] = row.value
    return ok(dict(grouped), "School settings")


@router.put("/settings", response_model=dict, dependencies=[Depends(permission_required("settings", "update"))])
async def bulk_update_settings(
    data: BulkSettingsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    school_id = _school_id_from_request(request, current_user)
    rows = await SchoolSettingsRepository(db).bulk_upsert(school_id, data.settings, str(current_user.id))
    return ok(rows, "School settings updated")


@router.get("/settings/{key}", response_model=dict)
async def get_setting(
    key: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    school_id = _school_id_from_request(request, current_user)
    value = await SchoolSettingsRepository(db).get_value(school_id, key)
    if value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    return ok({"key": key, "value": value}, "Setting value")


@router.put("/settings/{key}", response_model=dict, dependencies=[Depends(permission_required("settings", "update"))])
async def update_setting(
    key: str,
    data: SettingUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    school_id = _school_id_from_request(request, current_user)
    row = await SchoolSettingsRepository(db).upsert(school_id, key, data.value, str(current_user.id))
    return ok(row, "Setting updated")

