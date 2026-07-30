"""
Document upload & parse routes — Phase 1 concrete implementations.

API Spec: docs/08_api_specification/api_spec-v1.0.md §三
"""

from __future__ import annotations

import uuid
from pathlib import Path as FsPath
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from core.security import CurrentUser, get_current_user
from schemas.common import APIResponse, PaginatedData, PaginationParams
from schemas.document import (
    DocumentDetailResponse,
    DocumentListItem,
    UploadResponse,
)
from services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])

_settings = get_settings()


# ── Routes ──────────────────────────────────────────────────────────


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    document_type: str = Form(default="NDA"),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UploadResponse]:
    """Upload a document (PDF/DOCX) and validate through 5-layer chain.

    API Spec §3.1 — 5 层校验链:
    1. MIME type pre-check
    2. Magic byte validation (PDF: %PDF-, DOCX: PK)
    3. Encryption detection
    4. Corruption detection
    5. OCR detection
    """
    ext = FsPath(file.filename or "document.pdf").suffix.lower()
    storage_filename = f"{uuid.uuid4().hex}{ext}"
    storage_dir = _settings.STORAGE_LOCAL_PATH / "documents"
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / storage_filename

    service = DocumentService(db)
    document = await service.upload(
        file=file,
        storage_path=storage_path,
        title=title,
        document_type=document_type or "NDA",
    )
    return APIResponse(data=UploadResponse.model_validate(document))


@router.get("")
async def list_documents(
    status_filter: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PaginatedData[DocumentListItem]]:
    """List documents with optional status filter and pagination.

    API Spec §3.6
    """
    service = DocumentService(db)
    params = PaginationParams(page=page, size=size)
    result = await service.list_documents(status=status_filter, params=params)
    items = [DocumentListItem.model_validate(item) for item in result.items]
    return APIResponse(
        data=PaginatedData[DocumentListItem](
            page=result.page,
            size=result.size,
            total=result.total,
            items=items,
        )
    )


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DocumentDetailResponse]:
    """Get document details including parse task info.

    API Spec §3.2
    """
    service = DocumentService(db)
    document = await service.get_document(document_id)
    return APIResponse(data=DocumentDetailResponse.model_validate(document))


@router.get("/{document_id}/file")
async def get_document_file(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Download the original document file (PDF/DOCX).

    API Spec §3.3
    """
    service = DocumentService(db)
    document = await service.get_document(document_id)
    file_path = FsPath(document.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on storage")
    media_type_map = {
        "PDF": "application/pdf",
        "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    return FileResponse(
        path=str(file_path),
        media_type=media_type_map.get(document.format, "application/octet-stream"),
        filename=document.original_filename,
    )


@router.post("/{document_id}/parse", status_code=status.HTTP_202_ACCEPTED)
async def parse_document(
    document_id: str,
    playbook_id: Optional[str] = None,
    ocr_mode: str = "immediate",
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Start document parsing (clause extraction).

    API Spec §3.4 — to be fully implemented in Phase 2.
    """
    # Stub: Phase 2 will implement the full parse orchestration
    from models.document import Document, DocumentStatus
    from sqlalchemy import select

    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != DocumentStatus.UPLOADED:
        raise HTTPException(status_code=409, detail="Document must be in UPLOADED status")

    doc.status = DocumentStatus.PARSING
    await db.flush()

    return APIResponse(data={
        "document_id": document_id,
        "parse_task_id": "pending_phase2",
        "status": "queued",
        "message": "解析任务已入队 (Phase 2 实现)",
    })


@router.post("/{document_id}/parse/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_parse_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Retry a failed parse task (only if recoverable).

    API Spec §3.5 — to be fully implemented in Phase 2.
    """
    from models.document import Document, DocumentStatus
    from sqlalchemy import select

    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != DocumentStatus.FAILED:
        raise HTTPException(status_code=409, detail="Only FAILED documents can be retried")

    doc.status = DocumentStatus.PARSING
    await db.flush()

    return APIResponse(data={
        "document_id": document_id,
        "parse_task_id": "pending_phase2",
        "status": "queued",
        "message": "解析重试已入队 (Phase 2 实现)",
    })
