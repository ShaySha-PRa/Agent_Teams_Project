"""AuditLog — immutable hash-chained audit trail."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text, Enum
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import UUIDMixin, TimestampMixin, Base

if TYPE_CHECKING:
    from models.document import Document
    from models.review import ReviewDecision


# ── Audit-specific enums ───────────────────────────────────────────────


class OperationType(str, enum.Enum):
    """26 operation types covering the full document lifecycle."""

    UPLOAD = "UPLOAD"
    UPLOAD_FAILED = "UPLOAD_FAILED"
    PARSE_START = "PARSE_START"
    PARSE_PROGRESS = "PARSE_PROGRESS"
    PARSE_COMPLETE = "PARSE_COMPLETE"
    PARSE_FAILED = "PARSE_FAILED"
    PARSE_RETRY = "PARSE_RETRY"
    REVIEW_START = "REVIEW_START"
    REVIEW_PAUSE = "REVIEW_PAUSE"
    REVIEW_RESUME = "REVIEW_RESUME"
    REVIEW_CANCEL = "REVIEW_CANCEL"
    REVIEW_RETRY = "REVIEW_RETRY"
    REVIEW_COMPLETE = "REVIEW_COMPLETE"
    REVIEW_FAILED = "REVIEW_FAILED"
    REVIEW_TIMEOUT = "REVIEW_TIMEOUT"
    HUMAN_APPROVE = "HUMAN_APPROVE"
    HUMAN_EDIT = "HUMAN_EDIT"
    HUMAN_REJECT = "HUMAN_REJECT"
    MANUAL_ADD = "MANUAL_ADD"
    BATCH_CONFIRM = "BATCH_CONFIRM"
    SPOT_CHECK_ESCALATE = "SPOT_CHECK_ESCALATE"
    SPOT_CHECK_SAMPLE = "SPOT_CHECK_SAMPLE"
    FINAL_SUBMIT = "FINAL_SUBMIT"
    SAVE_DRAFT = "SAVE_DRAFT"
    REPORT_GENERATED = "REPORT_GENERATED"
    REPORT_SIGNED = "REPORT_SIGNED"


# ── Model ──────────────────────────────────────────────────────────────


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """Immutable audit log with SHA-256 hash chain for tamper evidence."""

    __tablename__ = "audit_logs"

    operation_type: Mapped[OperationType] = mapped_column(
        Enum(OperationType, name="operation_type"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    agent_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Entity references (soft, not enforced as FK for immutability)
    document_id: Mapped[str | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True, index=True
    )
    clause_id: Mapped[str | None] = mapped_column(
        ForeignKey("clauses.id"), nullable=True
    )
    risk_flag_id: Mapped[str | None] = mapped_column(
        ForeignKey("risk_flags.id"), nullable=True
    )
    decision_id: Mapped[str | None] = mapped_column(
        ForeignKey("review_decisions.id"), nullable=True, index=True
    )

    # Snapshots for reversibility
    before_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    after_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # SHA-256 hash chain
    prev_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    current_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    document: Mapped["Document"] = relationship("Document", back_populates="audit_logs")
    decision: Mapped["ReviewDecision"] = relationship(
        "ReviewDecision", back_populates="audit_logs"
    )
