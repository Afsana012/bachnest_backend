"""add roommate messages and connection inquiries table

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-09-20 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b3c4d5e6f7a8'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'roommate_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('roommate_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roommate_profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('recipient_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('sender_name', sa.String(length=255), nullable=False),
        sa.Column('sender_contact', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('reply', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_roommate_messages_profile_id', 'roommate_messages', ['roommate_profile_id'])
    op.create_index('ix_roommate_messages_sender_id', 'roommate_messages', ['sender_id'])
    op.create_index('ix_roommate_messages_recipient_user_id', 'roommate_messages', ['recipient_user_id'])


def downgrade():
    op.drop_index('ix_roommate_messages_recipient_user_id', table_name='roommate_messages')
    op.drop_index('ix_roommate_messages_sender_id', table_name='roommate_messages')
    op.drop_index('ix_roommate_messages_profile_id', table_name='roommate_messages')
    op.drop_table('roommate_messages')
