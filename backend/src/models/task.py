"""UploadTask, ParseTask, ReviewTask, StateTransition — async task models."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import UUIDMixin, TimestampMixin, Base

if TYPE_CHECKING:
    from models.document import Document
    from models.interrupt import InterruptSession


# ── Task-specific enums ────────────────────────────────────────────────


class UploadTaskStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class ParseTaskStatus(str, enum.Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewTaskStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    REVIEWING = "REVIEWING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class OperatorType(str, enum.Enum):
    HUMAN = "human"
    SYSTEM = "system"
    AGENT = "agent"


# ── Models ─────────────────────────────────────────────────────────────


class UploadTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "upload_tasks"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"), nullable=False, index=True
    )
    status: Mapped[UploadTaskStatus] = mapped_column(
        Enum(UploadTaskStatus, name="upload_task_status"),
        default=UploadTaskStatus.PENDING,
        nullable=False,
    )

    bytes_uploaded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    upload_speed: Mapped[float | None] = mapped_column(Float, nullable=True)

    format_validation_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    encryption_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    corruption_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ocr_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="upload_task")


class ParseTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "parse_tasks"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"), nullable=False, index=True
    )
    status: Mapped[ParseTaskStatus] = mapped_column(
        Enum(ParseTaskStatus, name="parse_task_status"),
        default=ParseTaskStatus.QUEUED,
        nullable=False,
    )

    # 4-agent progress dimensions (0.0–1.0)
    progress_clause_extraction: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_risk_analysis: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_compliance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_report: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    extracted_clause_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    recoverable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # LangGraph checkpointer token for resume
    checkpointer_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(256), nullable=True)

    playbook_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ocr_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="parse_task")


class ReviewTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "review_tasks"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"), nullable=False, index=True
    )
    status: Mapped[ReviewTaskStatus] = mapped_column(
        Enum(ReviewTaskStatus, name="review_task_status"),
        default=ReviewTaskStatus.QUEUED,
        nullable=False,
    )

    thread_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    checkpoint_id: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # 4-agent progress dimensions
    progress_risk_control: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_compliance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_obligation: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_report: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Risk counts after review
    high_risk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    medium_risk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_risk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    completed_clause_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_clause_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_partial_success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    fail_category: Mapped[str | None] = mapped_column(String(128), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="review_task")
    interrupt_sessions: Mapped[list["InterruptSession"]] = relationship(
        "InterruptSession", back_populates="review_task", lazy="selectin"
    )


class StateTransition(Base, UUIDMixin):
    """Immutable state-transition log with SHA-256 hash chain."""

    __tablename__ = "state_transitions"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"), nullable=False, index=True
    )
    from_status: Mapped[str] = mapped_column(String(64), nullable=False)
    to_status: Mapped[str] = mapped_column(String(64), nullable=False)
    trigger_reason: Mapped[str] = mapped_column(Text, nullable=False)
    operator_type: Mapped[OperatorType] = mapped_column(
        Enum(OperatorType, name="operator_type"), nullable=False
    )
    operator_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(  # type: ignore[valid-type]
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    prev_entry_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    document: Mapped["Document"] = relationship("Document", back_populates="state_transitions")
