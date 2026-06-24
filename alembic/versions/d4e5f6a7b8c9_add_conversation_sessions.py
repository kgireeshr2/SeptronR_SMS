"""Add conversation_sessions table for multi-turn chatbot flows.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-18 10:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'conversation_sessions',
        sa.Column('id', sa.String(100), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('school_id', sa.String(36), nullable=True),
        sa.Column('channel', sa.String(20), nullable=False, server_default='web'),
        sa.Column('current_flow', sa.String(60), nullable=True),
        sa.Column('current_step', sa.String(60), nullable=True),
        sa.Column('context_json', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("(NOW() + INTERVAL 24 HOUR)")),
    )
    op.create_index('ix_conv_session_user_channel', 'conversation_sessions',
                    ['user_id', 'channel'])
    op.create_index('ix_conv_session_school', 'conversation_sessions', ['school_id'])
    op.create_index('ix_conv_session_expires', 'conversation_sessions', ['expires_at'])


def downgrade() -> None:
    op.drop_index('ix_conv_session_expires', 'conversation_sessions')
    op.drop_index('ix_conv_session_school', 'conversation_sessions')
    op.drop_index('ix_conv_session_user_channel', 'conversation_sessions')
    op.drop_table('conversation_sessions')
