"""add_fee_v2_tables

Revision ID: a1b2c3d4e5f6
Revises: 827ca77eea72
Create Date: 2026-04-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '827ca77eea72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # v2_fee_types
    op.create_table(
        'v2_fee_types',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('school_id', 'name', name='uq_v2_fee_type_school_name'),
    )
    op.create_index('ix_v2_fee_types_school_id', 'v2_fee_types', ['school_id'])

    # v2_fee_groups
    op.create_table(
        'v2_fee_groups',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('school_id', 'name', name='uq_v2_fee_group_school_name'),
    )
    op.create_index('ix_v2_fee_groups_school_id', 'v2_fee_groups', ['school_id'])

    # v2_fee_group_items
    op.create_table(
        'v2_fee_group_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('fee_group_id', sa.Uuid(), nullable=False),
        sa.Column('fee_type_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['fee_group_id'], ['v2_fee_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fee_type_id'], ['v2_fee_types.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fee_group_id', 'fee_type_id', name='uq_v2_fee_group_item'),
    )
    op.create_index('ix_v2_fee_group_items_fee_group_id', 'v2_fee_group_items', ['fee_group_id'])
    op.create_index('ix_v2_fee_group_items_fee_type_id', 'v2_fee_group_items', ['fee_type_id'])

    # v2_fee_masters
    op.create_table(
        'v2_fee_masters',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('class_id', sa.Uuid(), nullable=False),
        sa.Column('academic_year_id', sa.Uuid(), nullable=False),
        sa.Column('fee_group_id', sa.Uuid(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['fee_group_id'], ['v2_fee_groups.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_v2_fee_masters_school_id', 'v2_fee_masters', ['school_id'])
    op.create_index('ix_v2_fee_masters_class_id', 'v2_fee_masters', ['class_id'])
    op.create_index('ix_v2_fee_masters_academic_year_id', 'v2_fee_masters', ['academic_year_id'])

    # v2_fee_master_items
    op.create_table(
        'v2_fee_master_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('fee_master_id', sa.Uuid(), nullable=False),
        sa.Column('fee_type_id', sa.Uuid(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.ForeignKeyConstraint(['fee_master_id'], ['v2_fee_masters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fee_type_id'], ['v2_fee_types.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fee_master_id', 'fee_type_id', name='uq_v2_fee_master_item'),
    )
    op.create_index('ix_v2_fee_master_items_fee_master_id', 'v2_fee_master_items', ['fee_master_id'])

    # v2_student_fee_assignments
    op.create_table(
        'v2_student_fee_assignments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('student_id', sa.Uuid(), nullable=False),
        sa.Column('fee_master_id', sa.Uuid(), nullable=False),
        sa.Column('academic_year_id', sa.Uuid(), nullable=False),
        sa.Column('assigned_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['fee_master_id'], ['v2_fee_masters.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'fee_master_id', 'academic_year_id', name='uq_v2_student_fee_master'),
    )
    op.create_index('ix_v2_student_fee_assignments_school_id', 'v2_student_fee_assignments', ['school_id'])
    op.create_index('ix_v2_student_fee_assignments_student_id', 'v2_student_fee_assignments', ['student_id'])

    # v2_fee_collections
    op.create_table(
        'v2_fee_collections',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('student_id', sa.Uuid(), nullable=False),
        sa.Column('fee_master_id', sa.Uuid(), nullable=False),
        sa.Column('academic_year_id', sa.Uuid(), nullable=False),
        sa.Column('receipt_number', sa.String(60), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('total_amount', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('total_discount', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('payment_method', sa.String(30), nullable=False),
        sa.Column('transaction_ref', sa.String(100), nullable=True),
        sa.Column('collected_by', sa.Uuid(), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('is_reversed', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('reversal_reason', sa.Text(), nullable=True),
        sa.Column('reversed_by', sa.Uuid(), nullable=True),
        sa.Column('reversed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['fee_master_id'], ['v2_fee_masters.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['collected_by'], ['users.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['reversed_by'], ['users.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('school_id', 'receipt_number', name='uq_v2_collection_receipt'),
    )
    op.create_index('ix_v2_fee_collections_school_id', 'v2_fee_collections', ['school_id'])
    op.create_index('ix_v2_fee_collections_student_id', 'v2_fee_collections', ['student_id'])

    # v2_fee_collection_items
    op.create_table(
        'v2_fee_collection_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('collection_id', sa.Uuid(), nullable=False),
        sa.Column('fee_type_id', sa.Uuid(), nullable=False),
        sa.Column('amount_paid', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('discount_amount', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('discount_reason', sa.String(200), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['v2_fee_collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fee_type_id'], ['v2_fee_types.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_v2_fee_collection_items_collection_id', 'v2_fee_collection_items', ['collection_id'])


def downgrade() -> None:
    op.drop_table('v2_fee_collection_items')
    op.drop_table('v2_fee_collections')
    op.drop_table('v2_student_fee_assignments')
    op.drop_table('v2_fee_master_items')
    op.drop_table('v2_fee_masters')
    op.drop_table('v2_fee_group_items')
    op.drop_table('v2_fee_groups')
    op.drop_table('v2_fee_types')
