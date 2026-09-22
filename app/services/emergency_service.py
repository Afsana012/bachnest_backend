"""Emergency service managing SOS incident lifecycles and resolution."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole
from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.models.booking import Tenancy
from app.models.emergency import EmergencyAlert
from app.models.property import Property
from app.models.user import User
from app.schemas.booking import EmergencyAlertOut, SOSRequest, SOSResolveRequest
from app.websockets.connection_manager import manager


class EmergencyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def trigger_sos(self, user: User, req: SOSRequest) -> EmergencyAlert:
        """Trigger an active emergency alert and broadcast via WebSocket."""
        # Find active tenancy for property context if exists
        tenancy_query = select(Tenancy.property_id).where(Tenancy.tenant_id == user.id).limit(1)
        property_id = (await self.db.execute(tenancy_query)).scalar_one_or_none()

        alert = EmergencyAlert(
            user_id=user.id,
            property_id=property_id,
            alert_type=req.alert_type,
            emergency_message=req.emergency_message,
            latitude=req.latitude,
            longitude=req.longitude,
            is_active=True,
        )
        self.db.add(alert)
        await self.db.flush()
        await self.db.refresh(alert)

        # Broadcast real-time WebSocket event
        try:
            await manager.broadcast({
                "event": "SOS_BROADCAST_ALERT",
                "data": {
                    "alert_id": str(alert.id),
                    "sender": {
                        "user_id": str(user.id),
                        "full_name": user.full_name,
                        "phone": user.phone,
                    },
                    "coordinates": {
                        "lat": alert.latitude,
                        "lng": alert.longitude,
                    },
                    "alert_type": alert.alert_type.value,
                    "message": alert.emergency_message,
                    "triggered_at": alert.created_at.isoformat(),
                }
            })
        except Exception:
            pass

        return alert

    async def get_emergency_by_id(self, alert_id: uuid.UUID, user: User) -> EmergencyAlert:
        """Retrieve emergency alert by ID."""
        query = select(EmergencyAlert).where(EmergencyAlert.id == alert_id)
        alert = (await self.db.execute(query)).scalar_one_or_none()
        if not alert:
            raise ResourceNotFoundError(message="Emergency alert not found")

        if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN) and alert.user_id != user.id:
            raise PermissionDeniedError(message="You do not have access to this emergency alert")

        return alert

    async def resolve_sos(self, alert_id: uuid.UUID, user: User, req: SOSResolveRequest) -> EmergencyAlert:
        """Mark an emergency alert as resolved."""
        alert = await self.get_emergency_by_id(alert_id, user)
        alert.is_active = False
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolved_by_id = user.id
        alert.resolution_notes = req.resolution_notes or "Resolved"

        await self.db.flush()
        await self.db.refresh(alert)
        return alert

    async def list_active_emergencies(self, only_active: bool = False) -> List[EmergencyAlertOut]:
        """Admin console query to view emergency alerts with user and property details."""
        query = (
            select(EmergencyAlert, User, Property)
            .join(User, EmergencyAlert.user_id == User.id)
            .outerjoin(Property, EmergencyAlert.property_id == Property.id)
        )
        if only_active:
            query = query.where(EmergencyAlert.is_active == True)

        query = query.order_by(EmergencyAlert.is_active.desc(), EmergencyAlert.created_at.desc())
        result = await self.db.execute(query)
        rows = result.all()

        items: List[EmergencyAlertOut] = []
        for alert, user, prop in rows:
            items.append(
                EmergencyAlertOut(
                    id=alert.id,
                    user_id=alert.user_id,
                    property_id=alert.property_id,
                    alert_type=alert.alert_type,
                    emergency_message=alert.emergency_message,
                    latitude=alert.latitude,
                    longitude=alert.longitude,
                    is_active=alert.is_active,
                    resolved_at=alert.resolved_at,
                    created_at=alert.created_at,
                    user_name=user.full_name if user else "Unknown User",
                    user_phone=user.phone if user else "",
                    property_title=prop.title if prop else None,
                    resolution_notes=alert.resolution_notes,
                )
            )
        return items
