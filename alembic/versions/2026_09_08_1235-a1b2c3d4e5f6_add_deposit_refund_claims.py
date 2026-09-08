"""add deposit refund claims table

Revision ID: a1b2c3d4e5f6
Revises: 9a5c2d1e3f4b
Create Date: 2026-09-08 12:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a1b2c3d4e5f6'
down_revision = '9a5c2d1e3f4b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE deposit_refund_status_enum AS ENUM (
                'REQUESTED',
                'INSPECTION_PENDING',
                'DEDUCTIONS_PROPOSED',
                'SETTLED',
                'DISPUTED',
                'REJECTED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.create_table(
        'deposit_refund_claims',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenancy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenancies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', postgresql.ENUM('REQUESTED', 'INSPECTION_PENDING', 'DEDUCTIONS_PROPOSED', 'SETTLED', 'DISPUTED', 'REJECTED', name='deposit_refund_status_enum', create_type=False), nullable=False, server_default='REQUESTED'),
        sa.Column('total_deposit_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('requested_refund_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('deduction_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('net_refund_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('deduction_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('tenant_payout_method', sa.String(length=50), nullable=False, server_default='BKASH'),
        sa.Column('tenant_payout_account', sa.String(length=100), nullable=False),
        sa.Column('move_out_date', sa.Date(), nullable=False),
        sa.Column('tenant_notes', sa.String(length=500), nullable=True),
        sa.Column('landlord_remarks', sa.String(length=500), nullable=True),
        sa.Column('transaction_reference', sa.String(length=100), nullable=True),
        sa.Column('settled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_deposit_refund_claims_tenancy_id', 'deposit_refund_claims', ['tenancy_id'])
    op.create_index('ix_deposit_refund_claims_tenant_id', 'deposit_refund_claims', ['tenant_id'])
    op.create_index('ix_deposit_refund_claims_owner_id', 'deposit_refund_claims', ['owner_id'])
    op.create_index('ix_deposit_refund_claims_status', 'deposit_refund_claims', ['status'])


def downgrade():
    op.drop_index('ix_deposit_refund_claims_status', table_name='deposit_refund_claims')
    op.drop_index('ix_deposit_refund_claims_owner_id', table_name='deposit_refund_claims')
    op.drop_index('ix_deposit_refund_claims_tenant_id', table_name='deposit_refund_claims')
    op.drop_index('ix_deposit_refund_claims_tenancy_id', table_name='deposit_refund_claims')
    op.drop_table('deposit_refund_claims')
    op.execute("DROP TYPE IF EXISTS deposit_refund_status_enum;")
