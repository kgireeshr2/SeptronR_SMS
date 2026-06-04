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
    # MySQL/MariaDB: ENUM values are part of the column definition.
    # Modify the column to add 'partial' to the enum values.
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect in ('mysql', 'mariadb'):
        op.execute(
            "ALTER TABLE personal_expenses MODIFY COLUMN status "
            "ENUM('pending', 'partial', 'paid', 'waived') NOT NULL DEFAULT 'pending'"
        )
    else:
        # PostgreSQL
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
