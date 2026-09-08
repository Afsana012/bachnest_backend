"""Add visit scheduling to bookings

Revision ID: 7e3f891a2b3c
Revises: 5cd2e320f79b
Create Date: 2026-09-08 10:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '7e3f891a2b3c'
down_revision = '5cd2e320f79b'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('bookings', sa.Column('preferred_visit_date', sa.Date(), nullable=True))
    op.add_column('bookings', sa.Column('visit_time_slot', sa.String(length=50), nullable=True))
    op.add_column('bookings', sa.Column('visit_notes', sa.String(length=500), nullable=True))
    op.add_column('bookings', sa.Column('visit_status', sa.String(length=30), nullable=True, server_default='SCHEDULED'))

def downgrade():
    op.drop_column('bookings', 'visit_status')
    op.drop_column('bookings', 'visit_notes')
    op.drop_column('bookings', 'visit_time_slot')
    op.drop_column('bookings', 'preferred_visit_date')
