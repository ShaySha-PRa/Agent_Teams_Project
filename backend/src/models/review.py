"""ReviewDecision + ReviewReport — human review decisions and final aggregation."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import UUIDMixin, TimestampMixin, Base

if TYPE_CHECKING:
    from models.risk_flag import RiskFlag
    from models.document import Document
    from models.audit import AuditLog


# ── Review-specific enums ──────────────────────────────────────────────


class DecisionType(str, enum.Enum):
    APPROVE = "APPROVE"
    EDIT = "EDIT"
    REJECT = "REJECT"
    MANUAL_ADD = "MANUAL_ADD"
    BATCH_CONFIRM = "BATCH_CONFIRM"
    SPOT_CHECK_CONFIRM = "SPOT_CHECK_CONFIRM"
    ESCALATE = "ESCALATE"


class SignStatus(str, enum.Enum):
    UNSIGNED = "UNSIGNED"
    SIGNED = "SIGNED"


# ── Models ─────────────────────────────────────────────────────────────


class ReviewDecision(Base, UUIDMixin, TimestampMixin):
    """Single human reviewer decision on a risk flag."""

    __tablename__ = "review_decisions"

    risk_flag_id: Mapped[str] = mapped_column(
        ForeignKey("risk_flags.id"), nullable=False, index=True
    )
    decision_type: Mapped[DecisionType] = mapped_column(
        Enum(DecisionType, name="decision_type"), nullable=False
    )
    reviewer_id: Mapped[str] = mapped_column(String(128), nullable=False)

    # Common
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # EDIT-specific
    modified_risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    modified_risk_category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    modified_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    # REJECT-specific
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # MANUAL_ADD-specific
    clause_location: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    manual_risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    manual_risk_category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # BATCH_CONFIRM-specific
    batched_risk_flag_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Versioning
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    risk_flag: Mapped["RiskFlag"] = relationship("RiskFlag", back_populates="decisions")
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="decision", lazy="selectin"
    )


class ReviewReport(Base, UUIDMixin, TimestampMixin):
    """Aggregated review report for one document (1:1 with Document)."""

    __tablename__ = "review_reports"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"), nullable=False, index=True, unique=True
    )
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sign_status: Mapped[SignStatus] = mapped_column(
        Enum(SignStatus, name="sign_status"), default=SignStatus.UNSIGNED, nullable=False
    )
    signer_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Risk aggregation
    high_confirmed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_amended: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    medium_auto_passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    medium_reviewed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_auto_passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_spot_checked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    manual_added: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="review_report")
