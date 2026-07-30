"""PlaybookRule + PlaybookMatch + ExplanationChain — review standards and matching."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import UUIDMixin, TimestampMixin, Base

if TYPE_CHECKING:
    from models.risk_flag import RiskFlag


# ── Playbook-specific enums ────────────────────────────────────────────


class MatchType(str, enum.Enum):
    EXACT = "EXACT"
    SEMANTIC = "SEMANTIC"
    PARTIAL = "PARTIAL"
    NO_MATCH = "NO_MATCH"


# ── Models ─────────────────────────────────────────────────────────────


class PlaybookRule(Base, UUIDMixin, TimestampMixin):
    """Enterprise-defined review standard (knowledge base)."""

    __tablename__ = "playbook_rules"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    applicable_doc_type: Mapped[str] = mapped_column(String(32), default="NDA", nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    risk_category: Mapped[str] = mapped_column(String(128), nullable=False)
    standard_clause_text: Mapped[str] = mapped_column(Text, nullable=False)
    rule_logic_description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    matches: Mapped[list["PlaybookMatch"]] = relationship(
        "PlaybookMatch", back_populates="playbook_rule", lazy="selectin"
    )


class PlaybookMatch(Base, UUIDMixin, TimestampMixin):
    """Match result between a clause and a playbook rule."""

    __tablename__ = "playbook_matches"

    risk_flag_id: Mapped[str] = mapped_column(
        ForeignKey("risk_flags.id"), nullable=False, index=True, unique=True
    )
    playbook_rule_id: Mapped[str] = mapped_column(
        ForeignKey("playbook_rules.id"), nullable=False, index=True
    )

    match_type: Mapped[MatchType] = mapped_column(
        Enum(MatchType, name="match_type"), nullable=False
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    diff_items: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    risk_flag: Mapped["RiskFlag"] = relationship("RiskFlag", back_populates="playbook_match")
    playbook_rule: Mapped["PlaybookRule"] = relationship(
        "PlaybookRule", back_populates="matches"
    )


class ExplanationChain(Base, UUIDMixin, TimestampMixin):
    """Full AI explanation chain for a risk flag."""

    __tablename__ = "explanation_chains"

    risk_flag_id: Mapped[str] = mapped_column(
        ForeignKey("risk_flags.id"), nullable=False, index=True, unique=True
    )
    explanation_steps: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    total_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    risk_flag: Mapped["RiskFlag"] = relationship("RiskFlag", back_populates="explanation_chain")
