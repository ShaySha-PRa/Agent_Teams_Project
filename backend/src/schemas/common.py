"""Pydantic v2 schemas — common response envelope and pagination."""

from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response envelope per spec §2.2."""

    code: int = Field(default=0, description="0 = success; non-zero maps to ErrorCode")
    message: str = Field(default="success")
    data: T | None = None
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex)


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="1-indexed page number")
    size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")


class PaginatedData(BaseModel, Generic[T]):
    """Paginated response wrapper per spec §2.4."""

    page: int
    size: int
    total: int
    items: list[T]
