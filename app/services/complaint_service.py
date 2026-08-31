"""Complaint service managing maintenance tickets, SLA tracking, and resolution workflows."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ComplaintStatus, SLA_HOURS_MAP, UserRole
from app.core.exceptions import InvalidBookingError, PermissionDeniedError, ResourceNotFoundError
from app.models.booking import Tenancy
from app.models.complaint import Complaint
from app.models.property import Property
from app.models.user import User
from app.schemas.booking import ComplaintCreateRequest, ComplaintStatusUpdate


class ComplaintService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_complaint(self, tenant: User, req: ComplaintCreateRequest) -> Complaint:
        """Submit a maintenance complaint and calculate SLA deadline."""
        sla_hours = SLA_HOURS_MAP.get(req.priority, 48)
        deadline = datetime.now(timezone.utc) + timedelta(hours=sla_hours)

        # Look up tenancy if exists
        tenancy_query = select(Tenancy).where(
            Tenancy.tenant_id == tenant.id,
            Tenancy.property_id == req.property_id,
        )
        tenancy = (await self.db.execute(tenancy_query)).scalar_one_or_none()

        complaint = Complaint(
            property_id=req.property_id,
            room_id=req.room_id,
            tenancy_id=tenancy.id if tenancy else None,
            tenant_id=tenant.id,
            title=req.title,
            description=req.description,
            category=req.category,
            priority=req.priority,
            status=ComplaintStatus.OPEN,
            sla_deadline=deadline,
            evidence_urls=req.evidence_urls,
        )
        self.db.add(complaint)
        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint

    async def list_complaints(
        self,
        user: User,
        status_filter: Optional[ComplaintStatus] = None,
    ) -> List[Complaint]:
        """List complaints for tenant, property owner, or admin."""
        if user.role == UserRole.OWNER:
            query = (
                select(Complaint)
                .join(Property, Property.id == Complaint.property_id)
                .where(Property.owner_id == user.id)
            )
        elif user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            query = select(Complaint)
        else:
            query = select(Complaint).where(Complaint.tenant_id == user.id)

        if status_filter:
            query = query.where(Complaint.status == status_filter)

        query = query.order_by(Complaint.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_complaint_by_id(self, complaint_id: uuid.UUID, user: User) -> Complaint:
        """Retrieve single complaint details with authorization checks."""
        query = select(Complaint).where(Complaint.id == complaint_id)
        complaint = (await self.db.execute(query)).scalar_one_or_none()
        if not complaint:
            raise ResourceNotFoundError(message="Complaint not found")

        if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            if complaint.tenant_id != user.id:
                prop_query = select(Property).where(Property.id == complaint.property_id)
                prop = (await self.db.execute(prop_query)).scalar_one_or_none()
                if not prop or prop.owner_id != user.id:
                    raise PermissionDeniedError(message="You do not have access to this complaint")

        return complaint

    async def update_status(
        self,
        complaint_id: uuid.UUID,
        user: User,
        req: ComplaintStatusUpdate,
    ) -> Complaint:
        """Update complaint status and record resolution metadata."""
        complaint = await self.get_complaint_by_id(complaint_id, user)

        complaint.status = req.status
        if req.resolution_notes:
            complaint.resolution_notes = req.resolution_notes
        if req.repair_cost is not None:
            complaint.repair_cost = req.repair_cost
        if req.cost_bearer:
            complaint.cost_bearer = req.cost_bearer

        if req.status in (ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED):
            complaint.resolved_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint

    async def reopen_complaint(
        self,
        complaint_id: uuid.UUID,
        tenant: User,
        reason: Optional[str] = None,
    ) -> Complaint:
        """Tenant reopens an unresolved complaint."""
        complaint = await self.get_complaint_by_id(complaint_id, tenant)
        if complaint.tenant_id != tenant.id:
            raise PermissionDeniedError(message="Only the reporting tenant can reopen this complaint")

        complaint.status = ComplaintStatus.REOPENED
        if reason:
            complaint.resolution_notes = f"[Reopened] {reason}"
        complaint.resolved_at = None

        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint
