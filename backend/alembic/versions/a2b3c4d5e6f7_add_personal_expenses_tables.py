"""add_personal_expenses_tables

Revision ID: a2b3c4d5e6f7
Revises: f6a7b8c9d0e1
Create Date: 2026-04-25 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a2b3c4d5e6f7'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
        ),
        {"t": table},
    )
    return result.scalar() > 0


def upgrade() -> None:
    if not _table_exists('personal_expense_categories'):
        op.create_table(
            'personal_expense_categories',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id']),
        sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_personal_expense_categories_school_id', 'personal_expense_categories', ['school_id'])

    # MySQL/MariaDB uses inline ENUM — no CREATE TYPE needed

    if not _table_exists('personal_expenses'):
        op.create_table(
            'personal_expenses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('student_id', sa.Uuid(), nullable=False),
        sa.Column('category_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('expense_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'paid', 'waived', name='personal_expense_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('paid_at', sa.Date(), nullable=True),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('collected_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id']),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['personal_expense_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['collected_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_personal_expenses_school_id', 'personal_expenses', ['school_id'])
        op.create_index('ix_personal_expenses_student_id', 'personal_expenses', ['student_id'])


def downgrade() -> None:
    op.drop_index('ix_personal_expenses_student_id', table_name='personal_expenses')
    op.drop_index('ix_personal_expenses_school_id', table_name='personal_expenses')
    op.drop_table('personal_expenses')
    # No DROP TYPE needed for MySQL
    op.drop_index('ix_personal_expense_categories_school_id', table_name='personal_expense_categories')
    op.drop_table('personal_expense_categories')
