"""InterruptSession — LangGraph HITL interrupt session record."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import UUIDMixin, Base

if TYPE_CHECKING:
    from models.task import ReviewTask


# ── Interrupt-specific enums ───────────────────────────────────────────


class InterruptPoint(str, enum.Enum):
    IP_1 = "IP-1"  # Individual risk flag review
    IP_2 = "IP-2"  # Batch medium-risk confirmation
    IP_3 = "IP-3"  # Final submit confirmation


class InterruptStatus(str, enum.Enum):
    WAITING = "waiting"
    RESOLVED = "resolved"
    TIMEOUT = "timeout"


# ── Model ──────────────────────────────────────────────────────────────


class InterruptSession(Base, UUIDMixin):
    """Records each LangGraph interrupt for audit and recovery.

    Does NOT inherit TimestampMixin because it has its own lifecycle timestamps
    (created_at, resumed_at, timeout_at) separate from the standard updated_at.
    """

    __tablename__ = "interrupt_sessions"

    review_task_id: Mapped[str] = mapped_column(
        ForeignKey("review_tasks.id"), nullable=False, index=True
    )
    interrupt_point: Mapped[InterruptPoint] = mapped_column(
        Enum(InterruptPoint, name="interrupt_point"), nullable=False
    )
    status: Mapped[InterruptStatus] = mapped_column(
        Enum(InterruptStatus, name="interrupt_status"),
        default=InterruptStatus.WAITING,
        nullable=False,
    )

    thread_id: Mapped[str] = mapped_column(String(256), nullable=False)
    checkpoint_id: Mapped[str | None] = mapped_column(String(256), nullable=True)

    interrupt_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    resume_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timeout_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    review_task: Mapped["ReviewTask"] = relationship(
        "ReviewTask", back_populates="interrupt_sessions"
    )
