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

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
        ),
        {"t": table, "c": column},
    )
    return result.scalar() > 0


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


def _add_column_if_missing(table: str, column_name: str, col_def):
    if not _column_exists(table, column_name):
        op.add_column(table, col_def)


def upgrade() -> None:
    # ── routes ──────────────────────────────────────────────────────────────
    _add_column_if_missing('routes', 'route_type', sa.Column('route_type', sa.String(10), nullable=False, server_default='both'))
    _add_column_if_missing('routes', 'starting_point_name', sa.Column('starting_point_name', sa.String(300), nullable=True))
    _add_column_if_missing('routes', 'ending_point_name', sa.Column('ending_point_name', sa.String(300), nullable=True))
    _add_column_if_missing('routes', 'start_latitude', sa.Column('start_latitude', sa.Numeric(10, 7), nullable=True))
    _add_column_if_missing('routes', 'start_longitude', sa.Column('start_longitude', sa.Numeric(10, 7), nullable=True))
    _add_column_if_missing('routes', 'end_latitude', sa.Column('end_latitude', sa.Numeric(10, 7), nullable=True))
    _add_column_if_missing('routes', 'end_longitude', sa.Column('end_longitude', sa.Numeric(10, 7), nullable=True))
    _add_column_if_missing('routes', 'morning_departure_time', sa.Column('morning_departure_time', sa.Time(), nullable=True))
    _add_column_if_missing('routes', 'school_arrival_time', sa.Column('school_arrival_time', sa.Time(), nullable=True))
    _add_column_if_missing('routes', 'evening_departure_time', sa.Column('evening_departure_time', sa.Time(), nullable=True))
    _add_column_if_missing('routes', 'total_distance_km', sa.Column('total_distance_km', sa.Numeric(6, 2), nullable=True))
    _add_column_if_missing('routes', 'estimated_duration_minutes', sa.Column('estimated_duration_minutes', sa.SmallInteger(), nullable=True))

    # ── stops ───────────────────────────────────────────────────────────────
    _add_column_if_missing('stops', 'address', sa.Column('address', sa.Text(), nullable=True))
    _add_column_if_missing('stops', 'landmark', sa.Column('landmark', sa.String(200), nullable=True))

    # ── vehicles ────────────────────────────────────────────────────────────
    _add_column_if_missing('vehicles', 'current_latitude', sa.Column('current_latitude', sa.Numeric(10, 7), nullable=True))
    _add_column_if_missing('vehicles', 'current_longitude', sa.Column('current_longitude', sa.Numeric(10, 7), nullable=True))
    _add_column_if_missing('vehicles', 'last_gps_update', sa.Column('last_gps_update', sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing('vehicles', 'vehicle_status', sa.Column('vehicle_status', sa.String(20), nullable=False, server_default='active'))
    _add_column_if_missing('vehicles', 'odometer_reading', sa.Column('odometer_reading', sa.Integer(), nullable=True))
    _add_column_if_missing('vehicles', 'color', sa.Column('color', sa.String(50), nullable=True))
    _add_column_if_missing('vehicles', 'chassis_number', sa.Column('chassis_number', sa.String(100), nullable=True))

    # ── vehicle_gps_logs (new table) ─────────────────────────────────────────
    if not _table_exists('vehicle_gps_logs'):
        op.create_table(
            'vehicle_gps_logs',
            sa.Column('id', sa.Uuid(), primary_key=True),
            sa.Column('school_id', sa.Uuid(), sa.ForeignKey('schools.id', ondelete='NO ACTION'), nullable=False),
            sa.Column('vehicle_id', sa.Uuid(), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
            sa.Column('latitude', sa.Numeric(10, 7), nullable=False),
            sa.Column('longitude', sa.Numeric(10, 7), nullable=False),
            sa.Column('speed_kmph', sa.Numeric(5, 2), nullable=True),
            sa.Column('heading_degrees', sa.SmallInteger(), nullable=True),
            sa.Column('altitude_meters', sa.Numeric(8, 2), nullable=True),
            sa.Column('accuracy_meters', sa.Numeric(6, 2), nullable=True),
            sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('source', sa.String(20), nullable=False, server_default='driver_app'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
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
