"""add driver details to vehicles

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-17 00:00:00.000000

"""
from __future__ import annotations
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('vehicles', sa.Column('driver_name', sa.String(200), nullable=True))
    op.add_column('vehicles', sa.Column('driver_phone', sa.String(20), nullable=True))
    op.add_column('vehicles', sa.Column('driver_license', sa.String(50), nullable=True))
    op.add_column('vehicles', sa.Column('conductor_name', sa.String(200), nullable=True))
    op.add_column('vehicles', sa.Column('conductor_phone', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('vehicles', 'conductor_phone')
    op.drop_column('vehicles', 'conductor_name')
    op.drop_column('vehicles', 'driver_license')
    op.drop_column('vehicles', 'driver_phone')
    op.drop_column('vehicles', 'driver_name')
