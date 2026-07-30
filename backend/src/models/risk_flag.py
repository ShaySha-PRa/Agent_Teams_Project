"""RiskFlag — AI risk assessment (core entity with 25 fields, 14 status + 15 category enums)."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import UUIDMixin, TimestampMixin, Base

if TYPE_CHECKING:
    from models.clause import Clause
    from models.document import Document
    from models.playbook import PlaybookMatch, ExplanationChain
    from models.review import ReviewDecision


# ── RiskFlag-specific enums ────────────────────────────────────────────


class RiskLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskCategory(str, enum.Enum):
    """15 risk categories."""

    # Clause-type aligned
    CONFIDENTIALITY = "保密义务"
    DURATION = "保密期限"
    EXCEPTION = "例外情形"
    BREACH_REMEDY = "违约救济"
    SURVIVAL = "存续条款"
    GOVERNING_LAW = "管辖法律"
    DISPUTE_RESOLUTION = "争议解决"
    NOTICE = "通知条款"
    ASSIGNABILITY = "可转让性"
    ENTIRE_AGREEMENT = "完整协议"
    # Additional risk dimensions
    COMPLIANCE = "合规风险"
    FINANCIAL = "财务风险"
    OPERATIONAL = "运营风险"
    LEGAL = "法律风险"
    REPUTATIONAL = "声誉风险"
    DATA_PRIVACY = "数据隐私"


class RiskFlagStatus(str, enum.Enum):
    """Risk flag lifecycle states — aligned with API spec + frontend types."""

    PENDING_REVIEW = "PENDING_REVIEW"
    CONFIRMED = "CONFIRMED"
    AMENDED = "AMENDED"
    REJECTED = "REJECTED"
    UNREVIEWED_AUTO_PASSED = "UNREVIEWED_AUTO_PASSED"
    REVIEWED_CONFIRMED = "REVIEWED_CONFIRMED"
    ESCALATED_TO_HIGH = "ESCALATED_TO_HIGH"
    RESOLVED = "RESOLVED"


class RiskFlagSource(str, enum.Enum):
    AI_GENERATED = "AI_GENERATED"
    MANUALLY_ADDED = "MANUALLY_ADDED"


# ── Model ──────────────────────────────────────────────────────────────


class RiskFlag(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "risk_flags"

    # Foreign keys
    clause_id: Mapped[str] = mapped_column(
        ForeignKey("clauses.id"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"), nullable=False, index=True
    )

    # Core classification
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risk_level"), nullable=False
    )
    risk_category: Mapped[RiskCategory] = mapped_column(
        Enum(RiskCategory, name="risk_category"), nullable=False
    )
    ai_confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Lifecycle
    status: Mapped[RiskFlagStatus] = mapped_column(
        Enum(RiskFlagStatus, name="risk_flag_status"),
        default=RiskFlagStatus.PENDING_REVIEW,
        nullable=False,
    )
    source: Mapped[RiskFlagSource] = mapped_column(
        Enum(RiskFlagSource, name="risk_flag_source"),
        default=RiskFlagSource.AI_GENERATED,
        nullable=False,
    )

    # Explanation fields (大文本字段)
    rationale_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    playbook_diff_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    regulation_reference: Mapped[str] = mapped_column(Text, nullable=False, default="")
    suggested_wording: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Escalation tracking (irreversible)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalated_from: Mapped[str | None] = mapped_column(String(16), nullable=True)
    sampled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Reviewer tracking
    reviewed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(128), nullable=True)  # v2 multi-reviewer

    # ── Relationships ─────────────────────────────────────────────────
    clause: Mapped["Clause"] = relationship("Clause", back_populates="risk_flags")
    playbook_match: Mapped["PlaybookMatch | None"] = relationship(
        "PlaybookMatch", back_populates="risk_flag", uselist=False, lazy="selectin"
    )
    explanation_chain: Mapped["ExplanationChain | None"] = relationship(
        "ExplanationChain", back_populates="risk_flag", uselist=False, lazy="selectin"
    )
    decisions: Mapped[list["ReviewDecision"]] = relationship(
        "ReviewDecision", back_populates="risk_flag", lazy="selectin"
    )
