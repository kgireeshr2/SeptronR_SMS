"""add doc ids and credentials support

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-19 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── AdmissionForm: extra_metadata (extra IDs captured at intake) ──────
    with op.batch_alter_table("admission_forms") as batch:
        batch.add_column(sa.Column("extra_metadata", sa.JSON(), nullable=True))

    # ── Student: Aadhaar, PAN, APAAR/PEN ────────────────────────────────────
    with op.batch_alter_table("students") as batch:
        batch.add_column(sa.Column("aadhaar_number", sa.String(20), nullable=True))
        batch.add_column(sa.Column("pan_number", sa.String(15), nullable=True))
        batch.add_column(sa.Column("apaar_number", sa.String(30), nullable=True))  # APAAR / PEN

    # ── StudentParent: Aadhaar, PAN, Ration Card ─────────────────────────────
    with op.batch_alter_table("student_parents") as batch:
        batch.add_column(sa.Column("aadhaar_number", sa.String(20), nullable=True))
        batch.add_column(sa.Column("pan_number", sa.String(15), nullable=True))
        batch.add_column(sa.Column("ration_card_number", sa.String(30), nullable=True))

    # ── Staff: Aadhaar, PAN, Driving Licence ─────────────────────────────────
    with op.batch_alter_table("staff") as batch:
        batch.add_column(sa.Column("aadhaar_number", sa.String(20), nullable=True))
        batch.add_column(sa.Column("pan_number", sa.String(15), nullable=True))
        batch.add_column(sa.Column("driving_licence", sa.String(30), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("admission_forms") as batch:
        batch.drop_column("extra_metadata")

    with op.batch_alter_table("staff") as batch:
        batch.drop_column("driving_licence")
        batch.drop_column("pan_number")
        batch.drop_column("aadhaar_number")

    with op.batch_alter_table("student_parents") as batch:
        batch.drop_column("ration_card_number")
        batch.drop_column("pan_number")
        batch.drop_column("aadhaar_number")

    with op.batch_alter_table("students") as batch:
        batch.drop_column("apaar_number")
        batch.drop_column("pan_number")
        batch.drop_column("aadhaar_number")
