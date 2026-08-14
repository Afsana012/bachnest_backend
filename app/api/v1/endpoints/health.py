"""Health check endpoints for Docker, Kubernetes, and uptime monitoring."""

from fastapi import APIRouter, Depends, status
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_redis
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
    try:
        await db.execute(text("SELECT 1"))
        return StandardResponse(
            success=True,
            message="Database connection healthy",
            data={"status": "connected", "database": "postgresql"}
        )
    except Exception as e:
        return StandardResponse(
            success=False,
            message=f"Database connection error: {str(e)}",
            data={"status": "disconnected"}
        )


@router.get("/redis", response_model=StandardResponse[dict])
async def redis_health_check(redis_client: aioredis.Redis = Depends(get_redis)):
    """Redis cache connectivity check."""
    if not redis_client:
        return StandardResponse(
            success=False,
            message="Redis client unavailable",
            data={"status": "disconnected"}
        )
    try:
        await redis_client.ping()
        return StandardResponse(
            success=True,
            message="Redis connection healthy",
            data={"status": "connected"}
        )
    except Exception as e:
        return StandardResponse(
            success=False,
            message=f"Redis connection error: {str(e)}",
            data={"status": "disconnected"}
        )
