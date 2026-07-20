"""add is_default to notification_templates and relax unique constraint

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-20 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Drop old unique constraint (school_id, channels, event_trigger)
    with op.batch_alter_table("notification_templates") as batch_op:
        try:
            batch_op.drop_constraint("notif_templates_school_ch_evt_ux", type_="unique")
        except Exception:
            pass  # may not exist under this name in all DB backends

        # 2. Add is_default column
        batch_op.add_column(sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")))

        # 3. New unique constraint: (school_id, event_trigger, name)
        batch_op.create_unique_constraint(
            "notif_templates_school_evt_name_ux",
            ["school_id", "event_trigger", "name"],
        )


def downgrade() -> None:
    with op.batch_alter_table("notification_templates") as batch_op:
        batch_op.drop_constraint("notif_templates_school_evt_name_ux", type_="unique")
        batch_op.drop_column("is_default")
        batch_op.create_unique_constraint(
            "notif_templates_school_ch_evt_ux",
            ["school_id", "channels", "event_trigger"],
        )
