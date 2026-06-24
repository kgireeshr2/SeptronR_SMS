"""add public school website tables

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-06-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'c4d5e6f7a8b9'
down_revision = 'b3c4d5e6f7a8'
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    """Dialect-agnostic table existence check (works on PostgreSQL & MySQL)."""
    bind = op.get_bind()
    return sa.inspect(bind).has_table(table)


def _bool_default(value: bool):
    # Portable boolean server default
    return sa.text('true') if value else sa.text('false')


def upgrade() -> None:
    if not _table_exists('school_website_config'):
        op.create_table(
            'school_website_config',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('school_id', sa.Uuid(), nullable=False),
            sa.Column('is_published', sa.Boolean(), nullable=False, server_default=_bool_default(False)),
            sa.Column('sections', sa.JSON(), nullable=True),
            sa.Column('theme_color', sa.String(20), nullable=False, server_default='#1e40af'),
            sa.Column('secondary_color', sa.String(20), nullable=True),
            sa.Column('hero_title', sa.String(255), nullable=True),
            sa.Column('hero_subtitle', sa.String(500), nullable=True),
            sa.Column('hero_image_url', sa.Text(), nullable=True),
            sa.Column('about_content', sa.Text(), nullable=True),
            sa.Column('mission', sa.Text(), nullable=True),
            sa.Column('vision', sa.Text(), nullable=True),
            sa.Column('contact_email', sa.String(200), nullable=True),
            sa.Column('contact_phone', sa.String(50), nullable=True),
            sa.Column('contact_address', sa.Text(), nullable=True),
            sa.Column('map_embed_url', sa.Text(), nullable=True),
            sa.Column('social_links', sa.JSON(), nullable=True),
            sa.Column('seo_title', sa.String(255), nullable=True),
            sa.Column('seo_description', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_school_website_config_school_id', 'school_website_config', ['school_id'], unique=True)

    if not _table_exists('gallery_albums'):
        op.create_table(
            'gallery_albums',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('school_id', sa.Uuid(), nullable=False),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('cover_image_url', sa.Text(), nullable=True),
            sa.Column('is_published', sa.Boolean(), nullable=False, server_default=_bool_default(True)),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_gallery_albums_school_id', 'gallery_albums', ['school_id'])

    if not _table_exists('gallery_images'):
        op.create_table(
            'gallery_images',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('school_id', sa.Uuid(), nullable=False),
            sa.Column('album_id', sa.Uuid(), nullable=True),
            sa.Column('image_url', sa.Text(), nullable=False),
            sa.Column('caption', sa.String(300), nullable=True),
            sa.Column('is_published', sa.Boolean(), nullable=False, server_default=_bool_default(True)),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id']),
            sa.ForeignKeyConstraint(['album_id'], ['gallery_albums.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_gallery_images_school_id', 'gallery_images', ['school_id'])
        op.create_index('ix_gallery_images_album_id', 'gallery_images', ['album_id'])

    if not _table_exists('website_notices'):
        op.create_table(
            'website_notices',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('school_id', sa.Uuid(), nullable=False),
            sa.Column('title', sa.String(300), nullable=False),
            sa.Column('body', sa.Text(), nullable=True),
            sa.Column('category', sa.String(50), nullable=False, server_default='notice'),
            sa.Column('attachment_url', sa.Text(), nullable=True),
            sa.Column('publish_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_published', sa.Boolean(), nullable=False, server_default=_bool_default(True)),
            sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=_bool_default(False)),
            sa.Column('created_by', sa.Uuid(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id']),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_website_notices_school_id', 'website_notices', ['school_id'])

    if not _table_exists('website_events'):
        op.create_table(
            'website_events',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('school_id', sa.Uuid(), nullable=False),
            sa.Column('title', sa.String(300), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('event_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('location', sa.String(300), nullable=True),
            sa.Column('image_url', sa.Text(), nullable=True),
            sa.Column('is_published', sa.Boolean(), nullable=False, server_default=_bool_default(True)),
            sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=_bool_default(False)),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_website_events_school_id', 'website_events', ['school_id'])

    if not _table_exists('website_enquiries'):
        op.create_table(
            'website_enquiries',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('school_id', sa.Uuid(), nullable=False),
            sa.Column('name', sa.String(150), nullable=False),
            sa.Column('phone', sa.String(20), nullable=True),
            sa.Column('email', sa.String(200), nullable=True),
            sa.Column('subject', sa.String(255), nullable=True),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('status', sa.String(20), nullable=False, server_default='new'),
            sa.Column('source', sa.String(50), nullable=False, server_default='website'),
            sa.Column('responded_by', sa.Uuid(), nullable=True),
            sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id']),
            sa.ForeignKeyConstraint(['responded_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_website_enquiries_school_id', 'website_enquiries', ['school_id'])

    if not _table_exists('website_content_items'):
        op.create_table(
            'website_content_items',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('school_id', sa.Uuid(), nullable=False),
            sa.Column('section', sa.String(50), nullable=False),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('subtitle', sa.String(255), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('image_url', sa.Text(), nullable=True),
            sa.Column('link_url', sa.Text(), nullable=True),
            sa.Column('meta', sa.JSON(), nullable=True),
            sa.Column('is_published', sa.Boolean(), nullable=False, server_default=_bool_default(True)),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_website_content_items_school_id', 'website_content_items', ['school_id'])
        op.create_index('ix_website_content_items_section', 'website_content_items', ['section'])

    if not _table_exists('school_domains'):
        op.create_table(
            'school_domains',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('school_id', sa.Uuid(), nullable=False),
            sa.Column('hostname', sa.String(255), nullable=False),
            sa.Column('verification_token', sa.String(64), nullable=True),
            sa.Column('verification_method', sa.String(20), nullable=False, server_default='dns_txt'),
            sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=_bool_default(False)),
            sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=_bool_default(False)),
            sa.Column('ssl_status', sa.String(20), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_school_domains_school_id', 'school_domains', ['school_id'])
        op.create_index('ix_school_domains_hostname', 'school_domains', ['hostname'], unique=True)


def downgrade() -> None:
    for table, indexes in [
        ('school_domains', ['ix_school_domains_hostname', 'ix_school_domains_school_id']),
        ('website_content_items', ['ix_website_content_items_section', 'ix_website_content_items_school_id']),
        ('website_enquiries', ['ix_website_enquiries_school_id']),
        ('website_events', ['ix_website_events_school_id']),
        ('website_notices', ['ix_website_notices_school_id']),
        ('gallery_images', ['ix_gallery_images_album_id', 'ix_gallery_images_school_id']),
        ('gallery_albums', ['ix_gallery_albums_school_id']),
        ('school_website_config', ['ix_school_website_config_school_id']),
    ]:
        for idx in indexes:
            try:
                op.drop_index(idx, table_name=table)
            except Exception:
                pass
        op.drop_table(table)
