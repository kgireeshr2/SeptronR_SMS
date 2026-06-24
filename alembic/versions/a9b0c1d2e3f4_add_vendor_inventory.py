"""Add vendor inventory tables

Revision ID: a9b0c1d2e3f4
Revises: f6a7b8c9d0e1
Create Date: 2026-04-21 00:00:00.000000
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = 'a9b0c1d2e3f4'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── vendors ──────────────────────────────────────────────────────────────
    op.create_table(
        'vendors',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('contact_person', sa.String(200), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('gst_number', sa.String(20), nullable=True),
        sa.Column('bank_name', sa.String(200), nullable=True),
        sa.Column('bank_account', sa.String(50), nullable=True),
        sa.Column('bank_ifsc', sa.String(20), nullable=True),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_vendors_user_id', 'vendors', ['user_id'])

    # ── vendor_school_links ───────────────────────────────────────────────────
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

    # ── vendor_products ───────────────────────────────────────────────────────
    op.create_table(
        'vendor_products',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('vendor_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('sku', sa.String(100), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('unit', sa.String(50), nullable=False, server_default=sa.text("'pcs'")),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('purchase_price', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('selling_price', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_vendor_products_vendor_id', 'vendor_products', ['vendor_id'])

    # ── vendor_stock ──────────────────────────────────────────────────────────
    op.create_table(
        'vendor_stock',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('vendor_id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('product_id', sa.Uuid(), nullable=False),
        sa.Column('qty_available', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('qty_reserved', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['product_id'], ['vendor_products.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vendor_id', 'school_id', 'product_id', name='vs_vendor_school_product_ux'),
    )
    op.create_index('ix_vendor_stock_school_id', 'vendor_stock', ['school_id'])
    op.create_index('ix_vendor_stock_vendor_id', 'vendor_stock', ['vendor_id'])

    # ── vendor_invoices ───────────────────────────────────────────────────────
    op.create_table(
        'vendor_invoices',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('vendor_id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('invoice_number', sa.String(100), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('total_amount', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('paid_amount', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'unpaid'")),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_vendor_invoices_vendor_id', 'vendor_invoices', ['vendor_id'])
    op.create_index('ix_vendor_invoices_school_id', 'vendor_invoices', ['school_id'])

    # ── vendor_invoice_items ──────────────────────────────────────────────────
    op.create_table(
        'vendor_invoice_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('invoice_id', sa.Uuid(), nullable=False),
        sa.Column('product_id', sa.Uuid(), nullable=False),
        sa.Column('qty', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.BigInteger(), nullable=False),
        sa.Column('total', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['vendor_invoices.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['product_id'], ['vendor_products.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_vendor_invoice_items_invoice_id', 'vendor_invoice_items', ['invoice_id'])

    # ── vendor_sales ──────────────────────────────────────────────────────────
    op.create_table(
        'vendor_sales',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('vendor_id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('student_id', sa.Uuid(), nullable=True),
        sa.Column('sale_date', sa.Date(), nullable=False),
        sa.Column('total_amount', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('payment_mode', sa.String(50), nullable=False, server_default=sa.text("'cash'")),
        sa.Column('received_by', sa.Uuid(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['received_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_vendor_sales_vendor_id', 'vendor_sales', ['vendor_id'])
    op.create_index('ix_vendor_sales_school_id', 'vendor_sales', ['school_id'])
    op.create_index('ix_vendor_sales_student_id', 'vendor_sales', ['student_id'])

    # ── vendor_sale_items ─────────────────────────────────────────────────────
    op.create_table(
        'vendor_sale_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('sale_id', sa.Uuid(), nullable=False),
        sa.Column('product_id', sa.Uuid(), nullable=False),
        sa.Column('qty', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.BigInteger(), nullable=False),
        sa.Column('total', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['sale_id'], ['vendor_sales.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['product_id'], ['vendor_products.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_vendor_sale_items_sale_id', 'vendor_sale_items', ['sale_id'])

    # ── vendor_payments ───────────────────────────────────────────────────────
    op.create_table(
        'vendor_payments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('vendor_id', sa.Uuid(), nullable=False),
        sa.Column('school_id', sa.Uuid(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('direction', sa.String(20), nullable=False, server_default=sa.text("'to_vendor'")),
        sa.Column('payment_mode', sa.String(50), nullable=False, server_default=sa.text("'bank_transfer'")),
        sa.Column('reference', sa.String(200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recorded_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_vendor_payments_vendor_id', 'vendor_payments', ['vendor_id'])
    op.create_index('ix_vendor_payments_school_id', 'vendor_payments', ['school_id'])


def downgrade() -> None:
    op.drop_table('vendor_payments')
    op.drop_table('vendor_sale_items')
    op.drop_table('vendor_sales')
    op.drop_table('vendor_invoice_items')
    op.drop_table('vendor_invoices')
    op.drop_table('vendor_stock')
    op.drop_table('vendor_products')
    op.drop_table('vendor_school_links')
    op.drop_table('vendors')
