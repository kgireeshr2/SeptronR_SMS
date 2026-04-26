"""personal_expenses: add paid_amount column and partial status

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-04-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'b3c4d5e6f7a8'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'partial' to the personal_expense_status enum
    # PostgreSQL 12+ supports this inside a transaction, but to be safe
    # we use the COMMIT trick via raw execute
    op.execute("ALTER TYPE personal_expense_status ADD VALUE IF NOT EXISTS 'partial' BEFORE 'paid'")

    # Add paid_amount column (what has actually been collected so far)
    op.add_column(
        'personal_expenses',
        sa.Column('paid_amount', sa.Numeric(12, 2), nullable=False, server_default='0')
    )

    # Back-fill paid_amount = amount for existing 'paid' records
    op.execute(
        "UPDATE personal_expenses SET paid_amount = amount WHERE status = 'paid'"
    )


def downgrade() -> None:
    op.drop_column('personal_expenses', 'paid_amount')
    # Note: PostgreSQL does not support removing enum values,
    # so we cannot cleanly revert the enum change.
