"""DeclarativeBase and reusable mixins for all models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base."""

    __abstract__ = True


class UUIDMixin:
    """UUID v4 primary key, assigned at the application layer (not the DB)."""

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: uuid.uuid4().hex,
        index=True,
    )


class TimestampMixin:
    """created_at / updated_at columns with server defaults."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
