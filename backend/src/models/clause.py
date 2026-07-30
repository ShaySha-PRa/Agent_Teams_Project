"""Clause + ClauseLocation — extracted structured clause and its position."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import UUIDMixin, TimestampMixin, Base

if TYPE_CHECKING:
    from models.document import Document
    from models.risk_flag import RiskFlag


# ── Clause-specific enums ──────────────────────────────────────────────


class ClauseType(str, enum.Enum):
    CONFIDENTIALITY = "保密义务"
    DURATION = "保密期限"
    EXCEPTION = "例外情形"
    BREACH_REMEDY = "违约救济"
    SURVIVAL = "存续条款"
    GOVERNING_LAW = "管辖法律"
    DISPUTE = "争议解决"
    NOTICE = "通知条款"
    ASSIGNABILITY = "可转让性"
    ENTIRE_AGREEMENT = "完整协议"


class ClauseSource(str, enum.Enum):
    AI = "AI"
    MANUAL = "MANUAL"


# ── Models ─────────────────────────────────────────────────────────────


class Clause(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "clauses"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"), nullable=False, index=True
    )
    clause_type: Mapped[ClauseType] = mapped_column(
        Enum(ClauseType, name="clause_type"), nullable=False
    )
    clause_text: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[ClauseSource] = mapped_column(
        Enum(ClauseSource, name="clause_source"), default=ClauseSource.AI, nullable=False
    )

    # Quick access to most-used location fields (denormalised for performance)
    page_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    paragraph_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    char_offset_start: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    char_offset_end: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    document: Mapped["Document"] = relationship("Document", back_populates="clauses")
    location: Mapped["ClauseLocation | None"] = relationship(
        "ClauseLocation", back_populates="clause", uselist=False, lazy="selectin"
    )
    risk_flags: Mapped[list["RiskFlag"]] = relationship(
        "RiskFlag", back_populates="clause", lazy="selectin"
    )


class ClauseLocation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "clause_locations"

    clause_id: Mapped[str] = mapped_column(
        ForeignKey("clauses.id"), nullable=False, index=True, unique=True
    )

    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    paragraph_number: Mapped[int] = mapped_column(Integer, nullable=False)
    line_number_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_number_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_offset_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_offset_end: Mapped[int] = mapped_column(Integer, nullable=False)
    bounding_box: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    text_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    clause: Mapped["Clause"] = relationship("Clause", back_populates="location")
