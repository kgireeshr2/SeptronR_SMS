"""add student contact and extended fields

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-04-26 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add contact & extended profile fields to students table
    op.add_column('students', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('students', sa.Column('email', sa.String(200), nullable=True))
    op.add_column('students', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('students', sa.Column('city', sa.String(100), nullable=True))
    op.add_column('students', sa.Column('state', sa.String(60), nullable=True))
    op.add_column('students', sa.Column('pincode', sa.String(10), nullable=True))
    op.add_column('students', sa.Column('caste', sa.String(100), nullable=True))
    op.add_column('students', sa.Column('mother_tongue', sa.String(60), nullable=True))
    op.add_column('students', sa.Column('previous_school', sa.String(200), nullable=True))
    op.add_column('students', sa.Column('emergency_contact_name', sa.String(200), nullable=True))
    op.add_column('students', sa.Column('emergency_contact_phone', sa.String(20), nullable=True))
    op.add_column('students', sa.Column('emergency_contact_relation', sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column('students', 'emergency_contact_relation')
    op.drop_column('students', 'emergency_contact_phone')
    op.drop_column('students', 'emergency_contact_name')
    op.drop_column('students', 'previous_school')
    op.drop_column('students', 'mother_tongue')
    op.drop_column('students', 'caste')
    op.drop_column('students', 'pincode')
    op.drop_column('students', 'state')
    op.drop_column('students', 'city')
    op.drop_column('students', 'address')
    op.drop_column('students', 'email')
    op.drop_column('students', 'phone')
