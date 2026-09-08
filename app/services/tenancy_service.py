from datetime import datetime, timezone
"""Tenancy service managing active rental agreements, notice periods, and move-outs."""

from typing import List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import AgreementStatus, TenancyStatus, UserRole
from app.core.exceptions import BadRequestError, InvalidBookingError, PermissionDeniedError, ResourceNotFoundError
from app.models.booking import Tenancy
from app.models.room import Room, RoomSeat
from app.models.user import User
from app.schemas.booking import AgreementSignRequest, DigitalAgreementOut, TenancyNoticeRequest


class TenancyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_user_tenancies(self, user: User) -> List[Tenancy]:
        """List tenancies for tenant or owner."""
        if user.role == UserRole.OWNER:
            query = select(Tenancy).where(Tenancy.owner_id == user.id).order_by(Tenancy.created_at.desc())
        elif user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            query = select(Tenancy).order_by(Tenancy.created_at.desc())
        else:
            query = select(Tenancy).where(Tenancy.tenant_id == user.id).order_by(Tenancy.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_tenancy_by_id(self, tenancy_id: uuid.UUID, user: User) -> Tenancy:
        """Retrieve tenancy details with authorization checks."""
        query = select(Tenancy).where(Tenancy.id == tenancy_id)
        result = await self.db.execute(query)
        tenancy = result.scalar_one_or_none()
        if not tenancy:
            raise ResourceNotFoundError(message="Tenancy not found")

        if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            if tenancy.tenant_id != user.id and tenancy.owner_id != user.id:
                raise PermissionDeniedError(message="You do not have access to this tenancy agreement")

        return tenancy

    async def serve_notice(self, tenancy_id: uuid.UUID, user: User, req: TenancyNoticeRequest) -> Tenancy:
        """Tenant or Owner serves formal move-out notice."""
        tenancy = await self.get_tenancy_by_id(tenancy_id, user)
        if tenancy.status != TenancyStatus.ACTIVE:
            raise InvalidBookingError(message=f"Notice cannot be served on tenancy in status {tenancy.status.value}")

        tenancy.status = TenancyStatus.NOTICE_SERVED
        tenancy.lease_end_date = req.move_out_date

        await self.db.flush()
        await self.db.refresh(tenancy)
        return tenancy

    async def terminate_tenancy(self, tenancy_id: uuid.UUID, user: User) -> Tenancy:
        """Complete move-out and release room/seat inventory."""
        tenancy = await self.get_tenancy_by_id(tenancy_id, user)
        if tenancy.status in (TenancyStatus.TERMINATED, TenancyStatus.EVICTED):
            raise InvalidBookingError(message="Tenancy is already terminated")

        tenancy.status = TenancyStatus.TERMINATED
        tenancy.agreement_status = AgreementStatus.EXPIRED

        # Release seat if occupied
        if tenancy.seat_id:
            seat_query = select(RoomSeat).where(RoomSeat.id == tenancy.seat_id).with_for_update()
            seat = (await self.db.execute(seat_query)).scalar_one_or_none()
            if seat:
                seat.is_occupied = False

        # Decrement room occupancy
        if tenancy.room_id:
            room_query = select(Room).where(Room.id == tenancy.room_id).with_for_update()
            room = (await self.db.execute(room_query)).scalar_one_or_none()
            if room:
                room.current_occupancy = max(0, room.current_occupancy - 1)
                room.is_available = True

        await self.db.flush()
        await self.db.refresh(tenancy)
        return tenancy

    async def get_digital_agreement_data(self, tenancy_id: uuid.UUID, user: User) -> DigitalAgreementOut:
        query = (
            select(Tenancy)
            .options(
                selectinload(Tenancy.property),
                selectinload(Tenancy.room),
                selectinload(Tenancy.tenant).selectinload(User.kyc),
                selectinload(Tenancy.owner),
            )
            .where(Tenancy.id == tenancy_id)
        )
        result = await self.db.execute(query)
        tenancy = result.scalar_one_or_none()
        if not tenancy:
            raise ResourceNotFoundError(message="Tenancy agreement not found")

        if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            if tenancy.tenant_id != user.id and tenancy.owner_id != user.id:
                raise PermissionDeniedError(message="Not authorized to view this agreement")

        tenant_nid = None
        if tenancy.tenant and tenancy.tenant.kyc:
            tenant_nid = tenancy.tenant.kyc.id_number

        return DigitalAgreementOut(
            tenancy_id=tenancy.id,
            agreement_status=tenancy.agreement_status,
            property_title=tenancy.property.title if tenancy.property else "BachNest Property",
            property_address=tenancy.property.address_line if tenancy.property else "Dhaka, Bangladesh",
            area_neighborhood=tenancy.property.area_neighborhood if tenancy.property else "Dhaka",
            city=tenancy.property.city if tenancy.property else "Dhaka",
            room_number_or_name=tenancy.room.room_number_or_name if tenancy.room else "Allocated Unit",
            owner_name=tenancy.owner.full_name if tenancy.owner else "Landlord",
            owner_phone=tenancy.owner.phone if tenancy.owner else "",
            tenant_name=tenancy.tenant.full_name if tenancy.tenant else "Tenant",
            tenant_phone=tenancy.tenant.phone if tenancy.tenant else "",
            tenant_nid_or_id=tenant_nid,
            agreed_monthly_rent=tenancy.agreed_monthly_rent,
            agreed_security_deposit=tenancy.agreed_security_deposit,
            lease_start_date=tenancy.lease_start_date,
            lease_end_date=tenancy.lease_end_date,
            notice_period_days=tenancy.notice_period_days,
            gate_closing_time=tenancy.property.gate_closing_time if tenancy.property else "11:00 PM",
            visitor_policy=tenancy.property.visitor_policy if tenancy.property else "Allowed with prior notification",
            signed_at=tenancy.updated_at if tenancy.agreement_status == AgreementStatus.SIGNED else None,
            signature_name=tenancy.digital_agreement_url if tenancy.digital_agreement_url else None,
        )

    async def sign_digital_agreement(
        self, tenancy_id: uuid.UUID, user: User, req: AgreementSignRequest
    ) -> Tenancy:
        if not req.agreed_terms:
            raise BadRequestError(message="You must accept the agreement terms to execute the contract")

        query = select(Tenancy).where(Tenancy.id == tenancy_id)
        result = await self.db.execute(query)
        tenancy = result.scalar_one_or_none()
        if not tenancy:
            raise ResourceNotFoundError(message="Tenancy agreement not found")

        if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN) and tenancy.tenant_id != user.id:
            raise PermissionDeniedError(message="Only the designated tenant can execute this agreement")

        if tenancy.agreement_status == AgreementStatus.SIGNED:
            return tenancy

        tenancy.agreement_status = AgreementStatus.SIGNED
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        tenancy.digital_agreement_url = f"E-SIGNED BY {req.signature_name.strip().upper()} ({timestamp_str})"

        await self.db.flush()
        await self.db.refresh(tenancy)
        return tenancy
