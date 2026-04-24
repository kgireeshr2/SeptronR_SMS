"""Transport GPS tracking and route enhancements

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-17 10:00:00.000000

Changes:
- routes: add route_type, starting/ending point (name + lat/lng),
          morning_departure_time, school_arrival_time, evening_departure_time,
          total_distance_km, estimated_duration_minutes
- stops:  add address, landmark (pickup_time/drop_time already exist for morning/evening)
- vehicles: add current_latitude, current_longitude, last_gps_update,
            vehicle_status, odometer_reading, color, chassis_number
- new table: vehicle_gps_logs  (live GPS tracks)
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── routes ──────────────────────────────────────────────────────────────
    op.add_column('routes', sa.Column('route_type', sa.String(10), nullable=False, server_default='both'))
    op.add_column('routes', sa.Column('starting_point_name', sa.String(300), nullable=True))
    op.add_column('routes', sa.Column('ending_point_name', sa.String(300), nullable=True))
    op.add_column('routes', sa.Column('start_latitude', sa.Numeric(10, 7), nullable=True))
    op.add_column('routes', sa.Column('start_longitude', sa.Numeric(10, 7), nullable=True))
    op.add_column('routes', sa.Column('end_latitude', sa.Numeric(10, 7), nullable=True))
    op.add_column('routes', sa.Column('end_longitude', sa.Numeric(10, 7), nullable=True))
    op.add_column('routes', sa.Column('morning_departure_time', sa.Time(), nullable=True))
    op.add_column('routes', sa.Column('school_arrival_time', sa.Time(), nullable=True))
    op.add_column('routes', sa.Column('evening_departure_time', sa.Time(), nullable=True))
    op.add_column('routes', sa.Column('total_distance_km', sa.Numeric(6, 2), nullable=True))
    op.add_column('routes', sa.Column('estimated_duration_minutes', sa.SmallInteger(), nullable=True))

    # ── stops ───────────────────────────────────────────────────────────────
    op.add_column('stops', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('stops', sa.Column('landmark', sa.String(200), nullable=True))

    # ── vehicles ────────────────────────────────────────────────────────────
    op.add_column('vehicles', sa.Column('current_latitude', sa.Numeric(10, 7), nullable=True))
    op.add_column('vehicles', sa.Column('current_longitude', sa.Numeric(10, 7), nullable=True))
    op.add_column('vehicles', sa.Column('last_gps_update', sa.DateTime(timezone=True), nullable=True))
    op.add_column('vehicles', sa.Column('vehicle_status', sa.String(20), nullable=False, server_default='active'))
    op.add_column('vehicles', sa.Column('odometer_reading', sa.Integer(), nullable=True))
    op.add_column('vehicles', sa.Column('color', sa.String(50), nullable=True))
    op.add_column('vehicles', sa.Column('chassis_number', sa.String(100), nullable=True))

    # ── vehicle_gps_logs (new table) ─────────────────────────────────────────
    op.create_table(
        'vehicle_gps_logs',
        sa.Column('id', UNIQUEIDENTIFIER(), primary_key=True),
        sa.Column('school_id', UNIQUEIDENTIFIER(), sa.ForeignKey('schools.id', ondelete='NO ACTION'), nullable=False),
        sa.Column('vehicle_id', UNIQUEIDENTIFIER(), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('latitude', sa.Numeric(10, 7), nullable=False),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=False),
        sa.Column('speed_kmph', sa.Numeric(5, 2), nullable=True),
        sa.Column('heading_degrees', sa.SmallInteger(), nullable=True),
        sa.Column('altitude_meters', sa.Numeric(8, 2), nullable=True),
        sa.Column('accuracy_meters', sa.Numeric(6, 2), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(20), nullable=False, server_default='driver_app'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_vehicle_gps_logs_vehicle_id', 'vehicle_gps_logs', ['vehicle_id'])
    op.create_index('ix_vehicle_gps_logs_recorded_at', 'vehicle_gps_logs', ['recorded_at'])
    op.create_index('ix_vehicle_gps_logs_school_id', 'vehicle_gps_logs', ['school_id'])


def downgrade() -> None:
    op.drop_table('vehicle_gps_logs')

    for col in ['chassis_number', 'color', 'odometer_reading', 'vehicle_status',
                'last_gps_update', 'current_longitude', 'current_latitude']:
        op.drop_column('vehicles', col)

    for col in ['landmark', 'address']:
        op.drop_column('stops', col)

    for col in ['estimated_duration_minutes', 'total_distance_km', 'evening_departure_time',
                'school_arrival_time', 'morning_departure_time', 'end_longitude', 'end_latitude',
                'start_longitude', 'start_latitude', 'ending_point_name', 'starting_point_name',
                'route_type']:
        op.drop_column('routes', col)
