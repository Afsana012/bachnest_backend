"""KYC service handling identity verification submissions, status tracking, and admin moderation."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import KYCStatus
from app.core.exceptions import ConflictError, ResourceNotFoundError
from app.models.kyc import UserKYC
from app.models.user import User
from app.schemas.kyc import KYCAdminDecisionRequest, KYCSubmitRequest


class KYCService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_kyc(self, user: User, req: KYCSubmitRequest) -> UserKYC:
        """Submit KYC verification documents."""
        query = select(UserKYC).where(UserKYC.user_id == user.id)
        result = await self.db.execute(query)
        kyc_entry = result.scalar_one_or_none()

        if kyc_entry and kyc_entry.status == KYCStatus.APPROVED:
            raise ConflictError(message="KYC is already approved for this account")

        if not kyc_entry:
            kyc_entry = UserKYC(
                user_id=user.id,
                status=KYCStatus.PENDING,
                document_type=req.document_type,
                document_number=req.document_number,
                front_document_url=req.front_document_url,
                back_document_url=req.back_document_url,
                student_or_work_id_url=req.student_or_work_id_url,
            )
            self.db.add(kyc_entry)
        else:
            kyc_entry.status = KYCStatus.PENDING
            kyc_entry.document_type = req.document_type
            kyc_entry.document_number = req.document_number
            kyc_entry.front_document_url = req.front_document_url
            kyc_entry.back_document_url = req.back_document_url
            kyc_entry.student_or_work_id_url = req.student_or_work_id_url
            kyc_entry.rejection_reason = None

        await self.db.flush()
        await self.db.refresh(kyc_entry)
        return kyc_entry

    async def get_my_kyc(self, user: User) -> UserKYC:
        """Retrieve user's KYC submission."""
        query = select(UserKYC).where(UserKYC.user_id == user.id)
        result = await self.db.execute(query)
        kyc_entry = result.scalar_one_or_none()
        if not kyc_entry:
            raise ResourceNotFoundError(message="No KYC submission found for this user")
        return kyc_entry

    async def resubmit_kyc(self, user: User, kyc_id: uuid.UUID, req: KYCSubmitRequest) -> UserKYC:
        """Resubmit a rejected KYC record."""
        query = select(UserKYC).where(UserKYC.id == kyc_id, UserKYC.user_id == user.id)
        result = await self.db.execute(query)
        kyc_entry = result.scalar_one_or_none()
        if not kyc_entry:
            raise ResourceNotFoundError(message="KYC record not found")
        if kyc_entry.status == KYCStatus.APPROVED:
            raise ConflictError(message="KYC is already approved and cannot be resubmitted")

        kyc_entry.status = KYCStatus.PENDING
        kyc_entry.document_type = req.document_type
        kyc_entry.document_number = req.document_number
        kyc_entry.front_document_url = req.front_document_url
        kyc_entry.back_document_url = req.back_document_url
        kyc_entry.student_or_work_id_url = req.student_or_work_id_url
        kyc_entry.rejection_reason = None

        await self.db.flush()
        await self.db.refresh(kyc_entry)
        return kyc_entry

    async def list_pending_kyc(self, status_filter: Optional[KYCStatus] = None) -> List[UserKYC]:
        """Admin helper to list KYC submissions."""
        query = select(UserKYC)
        if status_filter:
            query = query.where(UserKYC.status == status_filter)
        else:
            query = query.where(UserKYC.status == KYCStatus.PENDING)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def admin_decision(self, kyc_id: uuid.UUID, req: KYCAdminDecisionRequest) -> UserKYC:
        """Admin approves or rejects a KYC submission."""
        query = select(UserKYC).where(UserKYC.id == kyc_id)
        result = await self.db.execute(query)
        kyc_entry = result.scalar_one_or_none()
        if not kyc_entry:
            raise ResourceNotFoundError(message="KYC submission not found")

        kyc_entry.status = req.decision
        if req.decision == KYCStatus.APPROVED:
            kyc_entry.verified_at = datetime.now(timezone.utc)
            kyc_entry.rejection_reason = None

            # Update User status
            user_query = select(User).where(User.id == kyc_entry.user_id)
            user = (await self.db.execute(user_query)).scalar_one_or_none()
            if user:
                user.is_kyc_verified = True
                user.trust_score = min(100.0, user.trust_score + 20.0)
        else:
            kyc_entry.rejection_reason = req.rejection_reason
            kyc_entry.verified_at = None

            user_query = select(User).where(User.id == kyc_entry.user_id)
            user = (await self.db.execute(user_query)).scalar_one_or_none()
            if user:
                user.is_kyc_verified = False

        await self.db.flush()
        await self.db.refresh(kyc_entry)
        return kyc_entry
