"""Custom typed domain exceptions and global exception handlers for BachNest."""

from typing import Any, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    """Base application exception with HTTP status code and domain error code."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class ResourceNotFoundError(AppException):
    def __init__(self, message: str = "Requested resource was not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class PermissionDeniedError(AppException):
    def __init__(self, message: str = "You do not have permission to perform this action", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class AuthenticationError(AppException):
    def __init__(self, message: str = "Invalid authentication credentials", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_FAILED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict occurred", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class InvalidStateTransitionError(AppException):
    def __init__(self, message: str = "Invalid state transition requested", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="INVALID_STATE_TRANSITION",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class KYCRequiredError(AppException):
    def __init__(self, message: str = "Verified KYC is required to perform this action", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="KYC_REQUIRED",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class InvalidBookingError(AppException):
    def __init__(self, message: str = "Invalid booking request or inventory unavailable", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="INVALID_BOOKING",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class PaymentVerificationError(AppException):
    def __init__(self, message: str = "Payment verification failed or invalid signature", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="PAYMENT_VERIFICATION_FAILED",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform JSON error handlers according to BachNest PRD format."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "error": {
                    "code": exc.code,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        details = []
        for error in exc.errors():
            loc = " -> ".join([str(l) for l in error.get("loc", []) if l != "body"])
            details.append({
                "field": loc or "request",
                "message": error.get("msg", "Invalid input value"),
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Validation failed",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "details": details,
                },
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": str(exc.detail),
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "details": None,
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An unexpected internal server error occurred",
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "details": str(exc) if app.debug else None,
                },
            },
        )
