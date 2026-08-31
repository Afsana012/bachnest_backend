"""Health check endpoints for Docker, Kubernetes, and uptime monitoring."""

import asyncio

from fastapi import APIRouter, Depends, status
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_redis
from app.core.config import settings
from app.core.net import masked_target
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=StandardResponse[dict])
async def health_check():
    """General application liveness health probe."""
    return StandardResponse(
        success=True,
        message="BachNest API is active and healthy",
        data={"status": "ok"}
    )


@router.get("/db", response_model=StandardResponse[dict])
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """PostgreSQL database connectivity check."""
    target = masked_target(settings.DATABASE_URL)
    try:
        await db.execute(text("SELECT 1"))
        return StandardResponse(
            success=True,
            message="Database connection healthy",
            data={"status": "connected", "database": "postgresql", "target": target}
        )
    except asyncio.TimeoutError:
        return StandardResponse(
            success=False,
            message=f"Database connect timed out: this container cannot reach {target}",
            data={"status": "disconnected", "target": target}
        )
    except Exception as e:
        detail = str(e) or type(e).__name__
        return StandardResponse(
            success=False,
            message=f"Database connection error: {detail}",
            data={"status": "disconnected", "target": target}
        )


@router.get("/redis", response_model=StandardResponse[dict])
async def redis_health_check(redis_client: aioredis.Redis = Depends(get_redis)):
    """Redis cache connectivity check."""
    target = masked_target(settings.REDIS_URL)
    if not redis_client:
        return StandardResponse(
            success=False,
            message="Redis client unavailable",
            data={"status": "disconnected", "target": target}
        )
    try:
        await redis_client.ping()
        return StandardResponse(
            success=True,
            message="Redis connection healthy",
            data={"status": "connected", "target": target}
        )
    except asyncio.TimeoutError:
        return StandardResponse(
            success=False,
            message=f"Redis connect timed out: this container cannot reach {target}",
            data={"status": "disconnected", "target": target}
        )
    except Exception as e:
        detail = str(e) or type(e).__name__
        return StandardResponse(
            success=False,
            message=f"Redis connection error: {detail}",
            data={"status": "disconnected", "target": target}
        )
