"""Pydantic v2 schemas for Document endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator


# ── Response schemas ───────────────────────────────────────────────────


class DocumentResponse(BaseModel):
    """Returned by GET /documents/{id} and POST /documents/upload."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., validation_alias="id")
    original_filename: str
    title: str
    document_type: str
    format: str
    file_size_bytes: int
    page_count: int
    status: str
    uploaded_at: datetime | None = Field(default=None)
    md5_hash: str
    ocr_status: str
    encryption_status: str


class ParseTaskSummary(BaseModel):
    """Lightweight parse-task sub-object embedded in document detail."""

    model_config = ConfigDict(from_attributes=True)

    parse_task_id: str = Field(..., validation_alias="id")
    status: str
    extracted_clause_count: int = 0


class DocumentDetailResponse(DocumentResponse):
    """Full document response including nested parse-task summary."""

    parse_task: ParseTaskSummary | None = None


class DocumentListItem(BaseModel):
    """Single row in the document list response."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., validation_alias="id")
    title: str
    document_type: str
    status: str
    uploaded_at: datetime | None = Field(default=None)
    risk_summary: "RiskSummary | None" = None


class RiskSummary(BaseModel):
    """Aggregated risk counts for list display."""

    high: int = 0
    medium: int = 0
    low: int = 0


class UploadResponse(DocumentResponse):
    """Response from POST /documents/upload (201)."""
    pass


class ParseStartResponse(BaseModel):
    """Response from POST /documents/{id}/parse (202)."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str
    parse_task_id: str
    status: str
    message: str


# ── Request schemas ────────────────────────────────────────────────────


class ParseRequest(BaseModel):
    """Request body for POST /documents/{id}/parse."""

    playbook_id: str | None = Field(default=None, description="Playbook ID, default NDA Standard")
    ocr_mode: str | None = Field(default="immediate", description="immediate | background")
