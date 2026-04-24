"""Make vendors school-scoped (add school_id, drop vendor_school_links)

Revision ID: b1c2d3e4f5a6
Revises: a9b0c1d2e3f4
Create Date: 2026-04-21 00:00:00.000000
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = 'b1c2d3e4f5a6'
down_revision = 'a9b0c1d2e3f4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add school_id column to vendors (nullable first so existing rows are ok)
    op.add_column('vendors', sa.Column('school_id', sa.Uuid(), nullable=True))

    # 2. Populate school_id from vendor_school_links (pick the first linked school per vendor)
    op.execute(
        """UPDATE vendors
           SET school_id = (
               SELECT school_id
               FROM vendor_school_links
               WHERE vendor_id = vendors.id
               ORDER BY created_at
            LIMIT 1)
           WHERE school_id IS NULL"""
    )

    # 3. Create index on vendors.school_id
    op.create_index('ix_vendors_school_id', 'vendors', ['school_id'])

    # 4. Drop vendor_school_links table (no longer needed)
    op.drop_index('ix_vsl_vendor_id', table_name='vendor_school_links')
    op.drop_index('ix_vsl_school_id', table_name='vendor_school_links')
    op.drop_table('vendor_school_links')


def downgrade() -> None:
    # Recreate vendor_school_links
    op.create_table(
        'vendor_school_links',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('vendor_id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('commission_pct', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vendor_id', 'school_id', name='vsl_vendor_school_ux'),
    )
    op.create_index('ix_vsl_vendor_id', 'vendor_school_links', ['vendor_id'])
    op.create_index('ix_vsl_school_id', 'vendor_school_links', ['school_id'])

    # Restore links from vendors.school_id
    op.execute(
        """INSERT INTO vendor_school_links (id, vendor_id, school_id, commission_pct, is_active, created_at, updated_at)
           SELECT gen_random_uuid(), id, school_id, 0, 1, NOW(), NOW()
           FROM vendors WHERE school_id IS NOT NULL"""
    )

    op.drop_index('ix_vendors_school_id', table_name='vendors')
    op.drop_column('vendors', 'school_id')
