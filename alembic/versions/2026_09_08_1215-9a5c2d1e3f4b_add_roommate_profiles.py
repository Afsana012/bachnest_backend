"""add roommate profiles table

Revision ID: 9a5c2d1e3f4b
Revises: 8f4b12c3e4d5
Create Date: 2026-09-08 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '9a5c2d1e3f4b'
down_revision = '8f4b12c3e4d5'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE roommate_looking_type_enum AS ENUM ('ROOM_WANTED', 'FLATSHARE', 'HAVE_ROOM_NEED_ROOMMATE');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE roommate_occupation_category_enum AS ENUM ('STUDENT', 'JOB_HOLDER', 'FREELANCER', 'OTHER');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.create_table(
        'roommate_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('gender', postgresql.ENUM('MALE', 'FEMALE', 'OTHER', name='gender_enum', create_type=False), nullable=False),
        sa.Column('occupation', sa.String(length=255), nullable=False),
        sa.Column('occupation_category', postgresql.ENUM('STUDENT', 'JOB_HOLDER', 'FREELANCER', 'OTHER', name='roommate_occupation_category_enum', create_type=False), nullable=False),
        sa.Column('institution_or_company', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('preferred_areas', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('budget_max', sa.Numeric(precision=10, scale=2), nullable=False, server_default='5000.00'),
        sa.Column('looking_for', postgresql.ENUM('ROOM_WANTED', 'FLATSHARE', 'HAVE_ROOM_NEED_ROOMMATE', name='roommate_looking_type_enum', create_type=False), nullable=False),
        sa.Column('move_in_date', sa.String(length=50), nullable=False, server_default='Immediate'),
        sa.Column('lifestyle_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('bio', sa.Text(), nullable=False, server_default=''),
        sa.Column('phone', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('phone_visible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_roommate_profiles_user_id', 'roommate_profiles', ['user_id'], unique=True)


def downgrade():
    op.drop_index('ix_roommate_profiles_user_id', table_name='roommate_profiles')
    op.drop_table('roommate_profiles')
    op.execute("DROP TYPE IF EXISTS roommate_looking_type_enum;")
    op.execute("DROP TYPE IF EXISTS roommate_occupation_category_enum;")
