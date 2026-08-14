"""Standard response envelope schemas adhering to BachNest PRD."""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema enabling ORM mode."""
    model_config = ConfigDict(from_attributes=True)


class StandardResponse(BaseModel, Generic[T]):
    """Standard success response format: {"success": true, "message": "...", "data": ...}"""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None


class ErrorDetailItem(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorObject(BaseModel):
    code: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response format: {"success": false, "message": "...", "error": ...}"""
    success: bool = False
    message: str
    error: ErrorObject


class PaginationMeta(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    total: int = Field(default=0, ge=0)
    total_pages: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated items response envelope."""
    success: bool = True
    message: str = "Items retrieved successfully"
    items: List[T] = Field(default_factory=list)
    meta: PaginationMeta
