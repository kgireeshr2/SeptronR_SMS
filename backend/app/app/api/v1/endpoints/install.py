"""
Installation API — one-time setup endpoint
POST /api/v1/install      — create DB schema + seed all data
GET  /api/v1/install/status — check if system is installed

Protected by INSTALL_SECRET_KEY from .env so it can't be run by anyone.
Once installed, the endpoint can be disabled by unsetting INSTALL_SECRET_KEY.
"""
from __future__ import annotations

import uuid
import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import engine, get_db, Base

router = APIRouter(prefix="/install", tags=["Installation"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _verify_token(secret: str):
    """Validate the install secret key."""
    expected = getattr(settings, "INSTALL_SECRET_KEY", "")
    if not expected:
        raise HTTPException(
            status_code=403,
            detail="Installation is disabled. Set INSTALL_SECRET_KEY in .env to enable."
        )
    if secret != expected:
        raise HTTPException(status_code=403, detail="Invalid install secret key.")


async def _is_installed(db: AsyncSession) -> bool:
    """Return True if the users table exists and has at least one super admin."""
    try:
        result = await db.execute(
            text("SELECT COUNT(*) FROM users WHERE is_super_admin = TRUE")
        )
        return (result.scalar() or 0) > 0
    except Exception:
        return False


# ── Request/Response models ───────────────────────────────────────────────────

class InstallRequest(BaseModel):
    secret_key: str
    admin_email: Optional[str] = None
    admin_username: Optional[str] = None
    admin_password: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/status")
async def install_status(db: AsyncSession = Depends(get_db)):
    """Check if the system has been installed."""
    installed = await _is_installed(db)
    return {
        "success": True,
        "installed": installed,
        "message": "System is installed and ready." if installed else "System not installed. POST /api/v1/install to set up."
    }


@router.post("")
async def install(payload: InstallRequest, db: AsyncSession = Depends(get_db)):
    """
    Run one-time installation:
    1. Creates all database tables
    2. Seeds all permissions (100+ across all modules)
    3. Creates system roles with correct permission sets
    4. Creates the super-admin user
    """
    _verify_token(payload.secret_key)

    if await _is_installed(db):
        return {
            "success": True,
            "message": "System is already installed.",
            "already_installed": True,
        }

    steps = []

    # ── Step 1: Enable uuid-ossp extension ───────────────────────────────────────
    try:
        async with engine.begin() as conn:
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        steps.append("PostgreSQL uuid-ossp extension enabled")
    except Exception as e:
        steps.append(f"uuid-ossp extension note: {str(e)[:100]}")

    # ── Step 2: Create all tables ───────────────────────────────────────────────
    try:
        # Import all models so metadata is populated
        import app.models  # noqa: F401 — registers all models
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        steps.append("Database schema created successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema creation failed: {str(e)}")

    # ── Step 3: Seed permissions ──────────────────────────────────────────────
    try:
        from app.scripts.seed_data import (
            seed_permissions, seed_roles, seed_super_admin
        )
        perm_map = await seed_permissions(db)
        steps.append(f"Seeded {len(perm_map)} permissions")

        role_map = await seed_roles(db, perm_map)
        steps.append(f"Seeded {len(role_map)} system roles")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Permission/role seeding failed: {str(e)}")

    # ── Step 4: Create super admin ────────────────────────────────────────────
    try:
        # Allow override via request body
        if payload.admin_email:
            settings.SUPER_ADMIN_EMAIL = payload.admin_email
        if payload.admin_username:
            settings.SUPER_ADMIN_USERNAME = payload.admin_username
        if payload.admin_password:
            settings.SUPER_ADMIN_PASSWORD = payload.admin_password

        await seed_super_admin(db, role_map)
        steps.append(f"Super admin created: {settings.SUPER_ADMIN_EMAIL}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Super admin creation failed: {str(e)}")

    return {
        "success": True,
        "message": "Installation completed successfully!",
        "steps": steps,
        "credentials": {
            "email": settings.SUPER_ADMIN_EMAIL,
            "username": settings.SUPER_ADMIN_USERNAME,
            "password": settings.SUPER_ADMIN_PASSWORD,
            "note": "Change the password after first login!"
        }
    }
