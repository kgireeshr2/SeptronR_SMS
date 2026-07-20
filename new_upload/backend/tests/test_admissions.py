"""
Round 2 — Admissions Tests
"""
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.auth import User
from app.models.school import School
from app.models.academic import AcademicYear
from app.models.classes import Class


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def school(db_session: AsyncSession) -> School:
    s = School(name="Admission Test School", slug="admission-test-school", is_active=True)
    db_session.add(s)
    await db_session.flush()
    return s


@pytest_asyncio.fixture
async def academic_year(db_session: AsyncSession, school: School) -> AcademicYear:
    ay = AcademicYear(
        school_id=str(school.id),
        name="2025-26",
        start_date=date(2025, 4, 1),
        end_date=date(2026, 3, 31),
        is_current=True,
    )
    db_session.add(ay)
    await db_session.flush()
    return ay


@pytest_asyncio.fixture
async def class_obj(db_session: AsyncSession, school: School, academic_year: AcademicYear) -> Class:
    c = Class(
        school_id=str(school.id),
        academic_year_id=str(academic_year.id),
        name="Class 1",
        is_active=True,
    )
    db_session.add(c)
    await db_session.flush()
    return c


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        school_id=None,
        username="adm_superadmin",
        email="adm_super@test.com",
        password_hash=hash_password("Admin@1234"),
        is_active=True,
        is_verified=True,
        is_super_admin=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient, admin_user: User, school: School):
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "adm_super@test.com", "password": "Admin@1234"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["data"]["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-School-Id": str(school.id),
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAdmissionPublicConfig:
    async def test_public_config_school_not_found(self, async_client: AsyncClient):
        """Non-existent school slug returns 404."""
        resp = await async_client.get("/api/v1/admissions/public-config/no-such-school")
        assert resp.status_code == 404

    async def test_public_config_no_active_year(
        self, async_client: AsyncClient, school: School
    ):
        """School with no active admission config returns 404."""
        resp = await async_client.get(
            f"/api/v1/admissions/public-config/{school.slug}"
        )
        assert resp.status_code == 404


class TestAdmissionConfig:
    async def test_get_config_unauthenticated(
        self, async_client: AsyncClient, school: School
    ):
        """Unauthenticated request to get config returns 401."""
        resp = await async_client.get(
            "/api/v1/admissions/config",
            headers={"X-School-Id": str(school.id)},
        )
        assert resp.status_code == 401

    async def test_upsert_and_get_config(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        academic_year: AcademicYear,
    ):
        """Admin can save and retrieve admission form config."""
        payload = {
            "academic_year_id": str(academic_year.id),
            "is_active": True,
            "fields_config": [],
            "required_documents": [{"name": "Birth Certificate", "required": True}],
        }
        put_resp = await async_client.put(
            "/api/v1/admissions/config", json=payload, headers=auth_headers
        )
        assert put_resp.status_code == 200, put_resp.text

        get_resp = await async_client.get(
            f"/api/v1/admissions/config?year_id={academic_year.id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 200
        data = get_resp.json()["data"]
        assert data["is_active"] is True


class TestAdmissionApplication:
    async def _activate_admissions(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        academic_year_id: str,
    ):
        """Helper: create an active admission config."""
        await async_client.put(
            "/api/v1/admissions/config",
            json={
                "academic_year_id": academic_year_id,
                "is_active": True,
                "fields_config": [],
                "required_documents": [],
            },
            headers=auth_headers,
        )

    async def test_submit_application(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        school: School,
        academic_year: AcademicYear,
        class_obj: Class,
    ):
        await self._activate_admissions(async_client, auth_headers, str(academic_year.id))
        resp = await async_client.post(
            "/api/v1/admissions/apply",
            data={
                "school_slug": school.slug,
                "academic_year_id": str(academic_year.id),
                "applicant_name": "John Doe",
                "date_of_birth": "2010-06-15",
                "gender": "male",
                "applying_for_class_id": str(class_obj.id),
                "parent_name": "Jane Doe",
                "parent_phone": "9876543210",
                # NOTE: no parent_email to avoid Celery task blocking on Redis
            },
        )
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()["data"]
        assert data["applicant_name"] == "John Doe"

    async def test_list_applications(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        school: School,
        academic_year: AcademicYear,
        class_obj: Class,
    ):
        """Admin can list admission applications (paginated)."""
        await self._activate_admissions(async_client, auth_headers, str(academic_year.id))
        # Submit one application
        await async_client.post(
            "/api/v1/admissions/apply",
            data={
                "school_slug": school.slug,
                "academic_year_id": str(academic_year.id),
                "applicant_name": "Alice Smith",
                "date_of_birth": "2011-03-22",
                "parent_name": "Bob Smith",
                "parent_phone": "9123456789",
            },
        )
        resp = await async_client.get("/api/v1/admissions", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        # Paginated response: data.items is the list
        data = resp.json()["data"]
        assert "items" in data
        assert isinstance(data["items"], list)

    async def test_review_application(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        school: School,
        academic_year: AcademicYear,
        class_obj: Class,
    ):
        """Admin can review (approve/reject) an application."""
        await self._activate_admissions(async_client, auth_headers, str(academic_year.id))
        app_resp = await async_client.post(
            "/api/v1/admissions/apply",
            data={
                "school_slug": school.slug,
                "academic_year_id": str(academic_year.id),
                "applicant_name": "Charlie Brown",
                "date_of_birth": "2012-07-10",
                "parent_name": "Sally Brown",
                "parent_phone": "9001234567",
            },
        )
        assert app_resp.status_code in (200, 201), app_resp.text
        app_id = app_resp.json()["data"]["id"]

        # Review  — PUT /{form_id}/review, status must be "approved"|"rejected"|"waitlisted"|"under_review"
        review_resp = await async_client.put(
            f"/api/v1/admissions/{app_id}/review",
            json={"status": "under_review", "remarks": "Reviewing candidate"},
            headers=auth_headers,
        )
        assert review_resp.status_code == 200, review_resp.text
