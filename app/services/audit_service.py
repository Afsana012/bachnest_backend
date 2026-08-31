"""Audit logging service for tracking security and state change events."""

from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AuditAction
from app.models.emergency import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action_type: AuditAction,
        entity_name: str,
        entity_id: Optional[uuid.UUID] = None,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> AuditLog:
        """Record an audit trail event."""
        log_entry = AuditLog(
            actor_id=actor_id,
            action_type=action_type,
            entity_name=entity_name,
            entity_id=entity_id,
            ip_address=ip_address,
            changes=details,
        )
        self.db.add(log_entry)
        await self.db.flush()
        return log_entry

    async def list_logs(self, limit: int = 50) -> List[AuditLog]:
        """Retrieve recent audit events for admin review."""
        query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
