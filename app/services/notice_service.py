"""Notice service managing digital building notices and tenant read receipts."""

from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import NoticePriority, TenancyStatus, UserRole
from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.models.booking import Tenancy
from app.models.complaint import Notice, NoticeRead
from app.models.property import Property
from app.models.user import User
from app.schemas.booking import NoticeCreateRequest, NoticeOut, NoticeUpdateRequest


class NoticeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notice(self, property_id: uuid.UUID, owner: User, req: NoticeCreateRequest) -> Notice:
        """Owner publishes a digital notice to building tenants."""
        prop_query = select(Property).where(Property.id == property_id)
        prop = (await self.db.execute(prop_query)).scalar_one_or_none()
        if not prop:
            raise ResourceNotFoundError(message="Property not found")

        if prop.owner_id != owner.id and owner.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(message="You do not own this property")

        notice = Notice(
            property_id=property_id,
            owner_id=owner.id,
            title=req.title,
            content=req.content,
            priority=req.priority,
            is_active=True,
        )
        self.db.add(notice)
        await self.db.flush()
        await self.db.refresh(notice)
        return notice

    async def list_property_notices(self, property_id: uuid.UUID) -> List[Notice]:
        """List active notices for a property."""
        query = (
            select(Notice)
            .where(Notice.property_id == property_id, Notice.is_active == True)
            .order_by(Notice.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_tenant_notices(self, tenant: User) -> List[NoticeOut]:
        """List notices for all active properties the tenant resides in."""
        tenancies_query = select(Tenancy).where(
            Tenancy.tenant_id == tenant.id,
            Tenancy.status.in_([TenancyStatus.ACTIVE, TenancyStatus.NOTICE_SERVED])
        )
        tenancies = (await self.db.execute(tenancies_query)).scalars().all()
        property_ids = [t.property_id for t in tenancies]

        if not property_ids:
            return []

        notices_query = (
            select(Notice)
            .where(Notice.property_id.in_(property_ids), Notice.is_active == True)
            .order_by(Notice.created_at.desc())
        )
        notices = (await self.db.execute(notices_query)).scalars().all()

        # Check read receipts
        read_query = select(NoticeRead.notice_id).where(NoticeRead.user_id == tenant.id)
        read_notice_ids = set((await self.db.execute(read_query)).scalars().all())

        return [
            NoticeOut(
                id=n.id,
                property_id=n.property_id,
                owner_id=n.owner_id,
                title=n.title,
                content=n.content,
                priority=n.priority,
                is_active=n.is_active,
                is_read=n.id in read_notice_ids,
                created_at=n.created_at,
            )
            for n in notices
        ]

    async def mark_read(self, notice_id: uuid.UUID, user: User) -> bool:
        """Mark a notice as read by tenant."""
        dup_query = select(NoticeRead).where(
            NoticeRead.notice_id == notice_id,
            NoticeRead.user_id == user.id
        )
        existing = (await self.db.execute(dup_query)).scalar_one_or_none()
        if not existing:
            read_receipt = NoticeRead(notice_id=notice_id, user_id=user.id)
            self.db.add(read_receipt)
            await self.db.flush()
        return True

    async def update_notice(self, notice_id: uuid.UUID, owner: User, req: NoticeUpdateRequest) -> Notice:
        """Update a published notice."""
        query = select(Notice).where(Notice.id == notice_id)
        notice = (await self.db.execute(query)).scalar_one_or_none()
        if not notice:
            raise ResourceNotFoundError(message="Notice not found")

        if notice.owner_id != owner.id and owner.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(message="You do not own this notice")

        for field, val in req.model_dump(exclude_unset=True).items():
            setattr(notice, field, val)

        await self.db.flush()
        await self.db.refresh(notice)
        return notice

    async def delete_notice(self, notice_id: uuid.UUID, owner: User) -> bool:
        """Delete a notice."""
        query = select(Notice).where(Notice.id == notice_id)
        notice = (await self.db.execute(query)).scalar_one_or_none()
        if not notice:
            raise ResourceNotFoundError(message="Notice not found")

        if notice.owner_id != owner.id and owner.role != UserRole.SUPER_ADMIN:
            raise PermissionDeniedError(message="You do not own this notice")

        await self.db.delete(notice)
        await self.db.flush()
        return True
