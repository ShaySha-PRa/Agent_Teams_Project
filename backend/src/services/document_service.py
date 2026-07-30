"""Document service — CRUD, upload, file management."""

from __future__ import annotations

import shutil
from pathlib import Path as FsPath
from typing import BinaryIO

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError
from models.clause import Clause
from models.document import (
    Document,
    DocumentStatus,
    DocumentFormat,
    EncryptionStatus,
    OCRStatus,
)
from models.risk_flag import RiskFlag, RiskLevel
from models.task import UploadTask, UploadTaskStatus
from schemas.common import PaginatedData, PaginationParams
from utils.file_validator import validate_file


class DocumentService:
    """Stateless service for Document CRUD and upload operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Upload ───────────────────────────────────────────────────────

    async def upload(
        self,
        file: UploadFile,
        storage_path: FsPath,
        title: str | None = None,
        document_type: str = "NDA",
    ) -> Document:
        """Validate, persist, and store an uploaded document."""
        # ── 5-layer validation ─────────────────────────────────────
        content = await file.read()
        file.file.seek(0)  # Reset for potential re-read

        # Re-wrap content as a simple file-like for the validator
        import io

        bio = io.BytesIO(content)
        validation_result = validate_file(
            bio, filename=file.filename or "document.pdf", content_type=file.content_type
        )

        # ── Persist file to disk ───────────────────────────────────
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(storage_path, "wb") as f:
            f.write(content)

        # ── Create Document record ─────────────────────────────────
        import uuid as _uuid
        doc_id = _uuid.uuid4().hex
        doc = Document(
            id=doc_id,
            original_filename=file.filename or "unknown",
            title=title or FsPath(file.filename or "document").stem,
            document_type=document_type,  # type: ignore[arg-type]
            format=validation_result["format"],  # type: ignore[arg-type]
            file_size_bytes=validation_result["file_size_bytes"],
            page_count=validation_result["page_count"],
            md5_hash=validation_result["md5_hash"],
            status=DocumentStatus.UPLOADED,
            ocr_status=validation_result["ocr_status"],  # type: ignore[arg-type]
            encryption_status=EncryptionStatus.NONE,
            storage_path=str(storage_path),
        )
        self.session.add(doc)

        # ── Create UploadTask record ───────────────────────────────
        upload_task = UploadTask(
            document_id=doc_id,
            status=UploadTaskStatus.COMPLETED,
            total_bytes=validation_result["file_size_bytes"],
            bytes_uploaded=validation_result["file_size_bytes"],
            format_validation_passed=True,
            encryption_detected=False,
            corruption_detected=False,
            ocr_detected=(validation_result["ocr_status"] == "NEEDED"),
        )
        self.session.add(upload_task)

        await self.session.flush()
        await self.session.refresh(doc)
        return doc

    # ── Queries ──────────────────────────────────────────────────────

    async def get_document(self, document_id: str) -> Document:
        """Get a single document by ID; raises NotFoundError if missing."""
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            raise NotFoundError("Document", document_id)
        return doc

    async def list_documents(
        self,
        status: str | None = None,
        params: PaginationParams | None = None,
    ) -> PaginatedData[Document]:
        """List documents with optional status filter and pagination.

        Includes a risk_summary subquery for the list view.
        """
        if params is None:
            params = PaginationParams()

        stmt = select(Document)

        if status:
            stmt = stmt.where(Document.status == status)

        stmt = stmt.order_by(Document.created_at.desc())

        # Count
        count_stmt = select(func.count()).select_from(Document)
        if status:
            count_stmt = count_stmt.where(Document.status == status)
        total: int = (await self.session.execute(count_stmt)).scalar_one()

        # Paginate
        offset = (params.page - 1) * params.size
        page_stmt = stmt.offset(offset).limit(params.size)
        rows = (await self.session.execute(page_stmt)).scalars().all()

        # Enrich each row with risk_summary
        items = []
        for doc in rows:
            # Fetch risk counts
            risk_stmt = (
                select(
                    RiskFlag.risk_level,
                    func.count(RiskFlag.id).label("cnt"),
                )
                .where(RiskFlag.document_id == doc.id)
                .group_by(RiskFlag.risk_level)
            )
            risk_rows = (await self.session.execute(risk_stmt)).all()
            risk_map = {row[0]: row[1] for row in risk_rows}
            doc.risk_summary = {  # type: ignore[attr-defined]
                "high": risk_map.get(RiskLevel.HIGH, 0),
                "medium": risk_map.get(RiskLevel.MEDIUM, 0),
                "low": risk_map.get(RiskLevel.LOW, 0),
            }
            items.append(doc)

        return PaginatedData(
            page=params.page,
            size=params.size,
            total=total,
            items=items,
        )

    # ── Update helpers ────────────────────────────────────────────────

    async def update_status(self, document_id: str, status: DocumentStatus) -> Document:
        """Update document status."""
        doc = await self.get_document(document_id)
        doc.status = status
        await self.session.flush()
        return doc
