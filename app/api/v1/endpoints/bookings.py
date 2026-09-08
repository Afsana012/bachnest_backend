"""Booking and Tenancy API endpoints."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_roles
from app.core.constants import UserRole
from app.models.user import User
from app.schemas.booking import (
    AgreementSignRequest,
    DigitalAgreementOut,
    BookingAdvancePayRequest,
    BookingCreateRequest,
    BookingDecisionRequest,
    BookingOut,
    TenancyNoticeRequest,
    TenancyOut,
)
from app.schemas.common import StandardResponse
from app.services.booking_service import BookingService
from app.services.tenancy_service import TenancyService

bookings_router = APIRouter(prefix="/bookings", tags=["Bookings"])
tenancies_router = APIRouter(prefix="/tenancies", tags=["Tenancies"])


# --- BOOKINGS ---
@bookings_router.post("/request", response_model=StandardResponse[BookingOut], status_code=status.HTTP_201_CREATED)
async def create_booking_request(
    req: BookingCreateRequest,
    current_user: User = Depends(require_roles(UserRole.BACHELOR)),
    db: AsyncSession = Depends(get_db),
):
    """Submit a room/seat rental booking request."""
    booking_service = BookingService(db)
    booking = await booking_service.create_booking_request(current_user, req)
    return StandardResponse(
        success=True,
        message="Booking request submitted to owner",
        data=BookingOut.model_validate(booking),
    )


@bookings_router.get("/me", response_model=StandardResponse[List[BookingOut]])
async def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List bookings belonging to the current tenant or owner's properties."""
    booking_service = BookingService(db)
    bookings = await booking_service.list_user_bookings(current_user)
    return StandardResponse(
        success=True,
        message="Bookings retrieved",
        data=[BookingOut.model_validate(b) for b in bookings],
    )


@bookings_router.get("/{booking_id}", response_model=StandardResponse[BookingOut])
async def get_booking_by_id(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed information about a specific booking."""
    booking_service = BookingService(db)
    booking = await booking_service.get_booking_by_id(booking_id, current_user)
    return StandardResponse(
        success=True,
        message="Booking details retrieved",
        data=BookingOut.model_validate(booking),
    )


@bookings_router.patch("/{booking_id}/decision", response_model=StandardResponse[BookingOut])
async def owner_booking_decision(
    booking_id: uuid.UUID,
    req: BookingDecisionRequest,
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Owner approves or rejects a booking request."""
    booking_service = BookingService(db)
    booking = await booking_service.owner_decision(booking_id, current_user, req)
    return StandardResponse(
        success=True,
        message=f"Booking request {booking.booking_status.value.lower()}",
        data=BookingOut.model_validate(booking),
    )


@bookings_router.post("/{booking_id}/cancel", response_model=StandardResponse[BookingOut])
async def cancel_booking(
    booking_id: uuid.UUID,
    reason: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending booking request."""
    booking_service = BookingService(db)
    booking = await booking_service.cancel_booking(booking_id, current_user, reason)
    return StandardResponse(
        success=True,
        message="Booking request cancelled",
        data=BookingOut.model_validate(booking),
    )


@bookings_router.patch("/{booking_id}/visit-confirm", response_model=StandardResponse[BookingOut])
async def confirm_property_visit(
    booking_id: uuid.UUID,
    remarks: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    booking_service = BookingService(db)
    booking = await booking_service.confirm_visit(booking_id, current_user, remarks)
    return StandardResponse(
        success=True,
        message="Property visit confirmed",
        data=BookingOut.model_validate(booking),
    )


@bookings_router.patch("/{booking_id}/mark-visited", response_model=StandardResponse[BookingOut])
async def mark_property_visited(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking_service = BookingService(db)
    booking = await booking_service.mark_visited(booking_id, current_user)
    return StandardResponse(
        success=True,
        message="Property marked as visited",
        data=BookingOut.model_validate(booking),
    )


@bookings_router.post("/{booking_id}/pay-advance", response_model=StandardResponse[BookingOut])
async def pay_booking_advance(
    booking_id: uuid.UUID,
    req: BookingAdvancePayRequest,
    current_user: User = Depends(require_roles(UserRole.BACHELOR, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    booking_service = BookingService(db)
    booking = await booking_service.pay_advance(booking_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Advance deposit paid successfully. Tenancy created.",
        data=BookingOut.model_validate(booking),
    )


# --- TENANCIES ---
@tenancies_router.get("/me", response_model=StandardResponse[List[TenancyOut]])
async def get_my_tenancies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve active or past tenancies for tenant or owner."""
    tenancy_service = TenancyService(db)
    tenancies = await tenancy_service.list_user_tenancies(current_user)
    return StandardResponse(
        success=True,
        message="Tenancies retrieved",
        data=[TenancyOut.model_validate(t) for t in tenancies],
    )


@tenancies_router.get("/{tenancy_id}", response_model=StandardResponse[TenancyOut])
async def get_tenancy_by_id(
    tenancy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve specific tenancy agreement details."""
    tenancy_service = TenancyService(db)
    tenancy = await tenancy_service.get_tenancy_by_id(tenancy_id, current_user)
    return StandardResponse(
        success=True,
        message="Tenancy details retrieved",
        data=TenancyOut.model_validate(tenancy),
    )


@tenancies_router.patch("/{tenancy_id}/notice", response_model=StandardResponse[TenancyOut])
async def serve_tenancy_notice(
    tenancy_id: uuid.UUID,
    req: TenancyNoticeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Serve a move-out notice on an active tenancy."""
    tenancy_service = TenancyService(db)
    tenancy = await tenancy_service.serve_notice(tenancy_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Move-out notice served successfully",
        data=TenancyOut.model_validate(tenancy),
    )


@tenancies_router.patch("/{tenancy_id}/terminate", response_model=StandardResponse[TenancyOut])
async def terminate_tenancy(
    tenancy_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Terminate tenancy and restore room/seat inventory availability."""
    tenancy_service = TenancyService(db)
    tenancy = await tenancy_service.terminate_tenancy(tenancy_id, current_user)
    return StandardResponse(
        success=True,
        message="Tenancy terminated and inventory released",
        data=TenancyOut.model_validate(tenancy),
    )


@tenancies_router.get("/{tenancy_id}/agreement", response_model=StandardResponse[DigitalAgreementOut])
async def get_digital_agreement(
    tenancy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve compiled legal tenancy contract and e-signature status."""
    tenancy_service = TenancyService(db)
    agreement = await tenancy_service.get_digital_agreement_data(tenancy_id, current_user)
    return StandardResponse(
        success=True,
        message="Digital agreement details compiled successfully",
        data=agreement,
    )


@tenancies_router.post("/{tenancy_id}/sign", response_model=StandardResponse[TenancyOut])
async def sign_digital_agreement(
    tenancy_id: uuid.UUID,
    req: AgreementSignRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """E-sign the digital tenancy contract and transition to SIGNED status."""
    tenancy_service = TenancyService(db)
    tenancy = await tenancy_service.sign_digital_agreement(tenancy_id, current_user, req)
    return StandardResponse(
        success=True,
        message="Tenancy agreement digitally executed and signed successfully",
        data=TenancyOut.model_validate(tenancy),
    )


@tenancies_router.get("/{tenancy_id}/dmp-form", response_model=StandardResponse[dict])
async def get_tenancy_dmp_form_data(
    tenancy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve verified tenancy particulars for Dhaka DMP Citizen Information Form."""
    from sqlalchemy import select
    from app.models.booking import Tenancy
    from app.models.kyc import UserKYC
    from app.models.property import Property
    from app.models.room import Room
    from app.models.user import User

    tenancy_query = select(Tenancy).where(Tenancy.id == tenancy_id)
    tenancy = (await db.execute(tenancy_query)).scalar_one_or_none()
    if not tenancy:
        return StandardResponse(success=False, message="Tenancy not found", data=None)

    # Tenant details
    tenant_query = select(User).where(User.id == tenancy.tenant_id)
    tenant = (await db.execute(tenant_query)).scalar_one_or_none()

    # Owner details
    owner_query = select(User).where(User.id == tenancy.owner_id)
    owner = (await db.execute(owner_query)).scalar_one_or_none()

    # Property details
    prop_query = select(Property).where(Property.id == tenancy.property_id)
    prop = (await db.execute(prop_query)).scalar_one_or_none()

    # Room details
    room_query = select(Room).where(Room.id == tenancy.room_id)
    room = (await db.execute(room_query)).scalar_one_or_none()

    # KYC details
    kyc_query = select(UserKYC).where(UserKYC.user_id == tenancy.tenant_id)
    kyc = (await db.execute(kyc_query)).scalar_one_or_none()

    data = {
        "tenancy_id": str(tenancy.id),
        "lease_start_date": str(tenancy.lease_start_date),
        "monthly_rent": float(tenancy.agreed_monthly_rent),
        "security_deposit": float(tenancy.agreed_security_deposit),
        "status": tenancy.status.value if hasattr(tenancy.status, "value") else str(tenancy.status),
        "tenant": {
            "id": str(tenant.id) if tenant else "",
            "full_name": tenant.full_name if tenant else "",
            "phone": tenant.phone if tenant else "",
            "email": tenant.email if tenant else "",
            "occupation": tenant.occupation if tenant else "Student / Professional",
            "institution_or_company": tenant.institution_or_company if tenant else "",
            "gender": tenant.gender.value if tenant and hasattr(tenant.gender, "value") else "OTHER",
            "nid_number": kyc.document_number if kyc else "",
            "is_kyc_verified": kyc.status.value == "APPROVED" if kyc and hasattr(kyc.status, "value") else False,
        },
        "owner": {
            "id": str(owner.id) if owner else "",
            "full_name": owner.full_name if owner else "",
            "phone": owner.phone if owner else "",
            "email": owner.email if owner else "",
        },
        "property": {
            "id": str(prop.id) if prop else "",
            "title": prop.title if prop else "",
            "address_line": prop.address_line if prop else "",
            "area_neighborhood": prop.area_neighborhood if prop else "",
            "city": prop.city if prop else "Dhaka",
            "flat_number": prop.flat_number if prop else "",
        },
        "room": {
            "id": str(room.id) if room else "",
            "room_number_or_name": room.room_number_or_name if room else "",
            "room_type": room.room_type.value if room and hasattr(room.room_type, "value") else "SINGLE",
        },
    }

    return StandardResponse(
        success=True,
        message="DMP form data retrieved",
        data=data,
    )
