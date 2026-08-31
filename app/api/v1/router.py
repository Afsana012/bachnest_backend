"""Central API Router for version 1 (/api/v1)."""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.billing import (
    admin_router,
    billing_router,
    complaints_router,
    emergency_router,
    notices_router,
    payments_router,
    reviews_router,
)
from app.api.v1.endpoints.bookings import bookings_router, tenancies_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.properties import owner_properties_router, properties_router, rooms_router, search_router
from app.api.v1.endpoints.users import admin_kyc_router, kyc_router, users_router

api_router = APIRouter()

# Include all modular routers
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(kyc_router)
api_router.include_router(admin_kyc_router)
api_router.include_router(properties_router)
api_router.include_router(owner_properties_router)
api_router.include_router(rooms_router)
api_router.include_router(search_router)
api_router.include_router(bookings_router)
api_router.include_router(tenancies_router)
api_router.include_router(billing_router)
api_router.include_router(payments_router)
api_router.include_router(complaints_router)
api_router.include_router(notices_router)
api_router.include_router(reviews_router)
api_router.include_router(emergency_router)
api_router.include_router(admin_router)
