"""Document — the core entity representing a single contract/legal document."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import UUIDMixin, TimestampMixin, Base

if TYPE_CHECKING:
    from models.clause import Clause
    from models.task import ParseTask, ReviewTask, StateTransition, UploadTask
    from models.audit import AuditLog
    from models.review import ReviewReport


# ── Document-specific enums ────────────────────────────────────────────


class DocumentStatus(str, enum.Enum):
    CREATED = "CREATED"
    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    PARSED = "PARSED"
    REVIEWING = "REVIEWING"
    REVIEWED = "REVIEWED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    DRAFT = "DRAFT"


class DocumentType(str, enum.Enum):
    NDA = "NDA"


class DocumentFormat(str, enum.Enum):
    PDF = "PDF"
    DOCX = "DOCX"


class OCRStatus(str, enum.Enum):
    NOT_NEEDED = "NOT_NEEDED"
    NEEDED = "NEEDED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EncryptionStatus(str, enum.Enum):
    NONE = "NONE"
    DETECTED = "DETECTED"


# ── Model ──────────────────────────────────────────────────────────────


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    # File metadata
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type"), default=DocumentType.NDA, nullable=False
    )
    format: Mapped[DocumentFormat] = mapped_column(
        Enum(DocumentFormat, name="document_format"), nullable=False
    )
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    md5_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        default=DocumentStatus.CREATED,
        nullable=False,
    )

    # Validation results
    ocr_status: Mapped[OCRStatus] = mapped_column(
        Enum(OCRStatus, name="ocr_status"),
        default=OCRStatus.NOT_NEEDED,
        nullable=False,
    )
    encryption_status: Mapped[EncryptionStatus] = mapped_column(
        Enum(EncryptionStatus, name="encryption_status"),
        default=EncryptionStatus.NONE,
        nullable=False,
    )

    # Storage
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    # LangGraph integration
    review_thread_id: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # ── Derived properties ─────────────────────────────────────────
    @property
    def uploaded_at(self) -> datetime | None:
        """Alias for created_at — the upload timestamp."""
        return self.created_at

    # ── Relationships ─────────────────────────────────────────────────
    upload_task: Mapped["UploadTask | None"] = relationship(
        "UploadTask", back_populates="document", uselist=False, lazy="selectin"
    )
    parse_task: Mapped["ParseTask | None"] = relationship(
        "ParseTask", back_populates="document", uselist=False, lazy="selectin"
    )
    review_task: Mapped["ReviewTask | None"] = relationship(
        "ReviewTask", back_populates="document", uselist=False, lazy="selectin"
    )
    clauses: Mapped[list["Clause"]] = relationship(
        "Clause", back_populates="document", lazy="selectin"
    )
    state_transitions: Mapped[list["StateTransition"]] = relationship(
        "StateTransition", back_populates="document", lazy="selectin"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="document", lazy="selectin"
    )
    review_report: Mapped["ReviewReport | None"] = relationship(
        "ReviewReport", back_populates="document", uselist=False, lazy="selectin"
    )
