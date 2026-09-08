"""Add parking spaces and parking bookings

Revision ID: 8f4b12c3e4d5
Revises: 7e3f891a2b3c
Create Date: 2026-09-08 10:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '8f4b12c3e4d5'
down_revision = '7e3f891a2b3c'
branch_labels = None
depends_on = None

def upgrade():
    # 1. parking_spaces table
    op.create_table(
        'parking_spaces',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('property_id', sa.UUID(), sa.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False),
        sa.Column('space_number_or_name', sa.String(length=100), nullable=False),
        sa.Column('vehicle_type', sa.Enum('BIKE', 'CAR', name='vehicle_type_enum'), nullable=False),
        sa.Column('monthly_rate', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('daily_rate', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_covered', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('has_cctv', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_parking_spaces_property_id', 'parking_spaces', ['property_id'])
    op.create_index('ix_parking_spaces_is_available', 'parking_spaces', ['is_available'])
    op.create_index('ix_parking_spaces_vehicle_type', 'parking_spaces', ['vehicle_type'])

    # 2. parking_bookings table
    op.create_table(
        'parking_bookings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parking_space_id', sa.UUID(), sa.ForeignKey('parking_spaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rental_plan', sa.Enum('DAILY', 'MONTHLY', name='parking_rental_plan_enum'), nullable=False),
        sa.Column('vehicle_registration_number', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'EXPIRED', 'CANCELLED', name='parking_booking_status_enum'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_parking_bookings_user_id', 'parking_bookings', ['user_id'])
    op.create_index('ix_parking_bookings_parking_space_id', 'parking_bookings', ['parking_space_id'])
    op.create_index('ix_parking_bookings_status', 'parking_bookings', ['status'])

def downgrade():
    op.drop_index('ix_parking_bookings_status', table_name='parking_bookings')
    op.drop_index('ix_parking_bookings_parking_space_id', table_name='parking_bookings')
    op.drop_index('ix_parking_bookings_user_id', table_name='parking_bookings')
    op.drop_table('parking_bookings')
    
    op.drop_index('ix_parking_spaces_vehicle_type', table_name='parking_spaces')
    op.drop_index('ix_parking_spaces_is_available', table_name='parking_spaces')
    op.drop_index('ix_parking_spaces_property_id', table_name='parking_spaces')
    op.drop_table('parking_spaces')
    
    op.execute('DROP TYPE IF EXISTS parking_booking_status_enum')
    op.execute('DROP TYPE IF EXISTS parking_rental_plan_enum')
    op.execute('DROP TYPE IF EXISTS vehicle_type_enum')
