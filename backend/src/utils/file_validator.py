"""5-layer file validation chain per API spec §3.1."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO

from core.exceptions import ErrorCode, FileValidationError

# Maximum file size: 50 MB
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
# Maximum page count
MAX_PAGE_COUNT = 200

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
}

# Magic bytes for format verification
MAGIC_BYTES = {
    "PDF": b"%PDF-",
    "DOCX": b"PK\x03\x04",
}


def validate_file(file: BinaryIO, filename: str, content_type: str | None) -> dict:
    """Run the 5-layer validation chain and return file metadata.

    Args:
        file: The uploaded file object (spooled to a temp file or in-memory).
        filename: Original filename from the client.
        content_type: MIME type reported by the client.

    Returns:
        dict with keys: format, file_size_bytes, page_count, md5_hash,
                        ocr_status, encryption_status.

    Raises:
        FileValidationError: On any validation failure.
    """
    # ── Layer 1: Extension whitelist ────────────────────────────────
    suffix = Path(filename).suffix.lower()
    if suffix not in (".pdf", ".docx"):
        raise FileValidationError(
            ErrorCode.UNSUPPORTED_FORMAT,
            f"Unsupported file extension '{suffix}'. Only .pdf and .docx are accepted.",
        )

    # ── Layer 2: MIME type check ────────────────────────────────────
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise FileValidationError(
            ErrorCode.UNSUPPORTED_FORMAT,
            f"Unsupported MIME type '{content_type}'. Only PDF and DOCX are accepted.",
        )

    # Read file content
    file.seek(0)
    content = file.read()
    file_size = len(content)
    file.seek(0)

    # ── Layer 3: File size ──────────────────────────────────────────
    if file_size < 1:
        raise FileValidationError(ErrorCode.FILE_CORRUPTED, "Uploaded file is empty.")
    if file_size > MAX_FILE_SIZE_BYTES:
        raise FileValidationError(
            ErrorCode.FILE_TOO_LARGE,
            f"File size ({file_size / 1024 / 1024:.1f} MB) exceeds the {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit.",
        )

    # ── Layer 4: Magic byte detection ───────────────────────────────
    detected_format = _detect_format(content)
    if detected_format is None:
        raise FileValidationError(
            ErrorCode.UNSUPPORTED_FORMAT,
            "File format could not be determined. Only PDF and DOCX are accepted.",
        )

    # ── Layer 5: Encryption & corruption detection ──────────────────
    encryption_status = _check_encryption(content, detected_format)
    if encryption_status == "DETECTED":
        raise FileValidationError(
            ErrorCode.FILE_ENCRYPTED,
            f"The {detected_format} file appears to be encrypted or password-protected. Please remove protection and re-upload.",
        )

    corruption = _check_corruption(content, detected_format)
    if corruption:
        raise FileValidationError(
            ErrorCode.FILE_CORRUPTED,
            f"The {detected_format} file appears to be corrupted. Please re-export the document and try again.",
        )

    # ── OCR detection ───────────────────────────────────────────────
    ocr_status = _detect_ocr_need(content, detected_format)

    # ── Page count estimation ───────────────────────────────────────
    page_count = _estimate_page_count(content, detected_format)

    if page_count > MAX_PAGE_COUNT:
        raise FileValidationError(
            ErrorCode.PAGE_LIMIT_EXCEEDED,
            f"Document has ~{page_count} pages, exceeding the {MAX_PAGE_COUNT}-page limit.",
        )

    # ── MD5 hash ────────────────────────────────────────────────────
    md5_hash = hashlib.md5(content).hexdigest()

    return {
        "format": detected_format,
        "file_size_bytes": file_size,
        "page_count": page_count,
        "md5_hash": md5_hash,
        "ocr_status": ocr_status,
        "encryption_status": "NONE",
    }


# ── Detection helpers ──────────────────────────────────────────────────


def _detect_format(content: bytes) -> str | None:
    """Identify file format from magic bytes."""
    for fmt, magic in MAGIC_BYTES.items():
        if content[: len(magic)] == magic:
            return fmt
    # Heuristic: ZIP-based formats (DOCX is a ZIP)
    if content[:2] == b"PK":
        # Could be DOCX — check for Word-specific internal paths
        if b"word/" in content[:4096].lower():
            return "DOCX"
    return None


def _check_encryption(content: bytes, fmt: str) -> str:
    """Detect encryption/password protection."""
    if fmt == "PDF":
        # Check for /Encrypt in PDF header area
        header = content[:4096].decode("latin-1", errors="ignore")
        if "/Encrypt" in header:
            return "DETECTED"
    elif fmt == "DOCX":
        # DOCX is a ZIP — check for encrypted package marker
        if b"EncryptedPackage" in content[:4096] or b"EncryptionInfo" in content[:4096]:
            return "DETECTED"
    return "NONE"


def _check_corruption(content: bytes, fmt: str) -> bool:
    """Basic structural integrity check."""
    if fmt == "PDF":
        # Must end with %%EOF (within last ~1KB)
        trailer = content[-1024:].decode("latin-1", errors="ignore")
        if "%%EOF" not in trailer:
            return True
        # Must have at least one xref table or stream
        if b"xref" not in content and b"/XRef" not in content:
            return True
    elif fmt == "DOCX":
        # DOCX is a ZIP — check ZIP end-of-central-directory signature
        if len(content) < 22:
            return True
        # Search for EOCD signature backwards
        if b"PK\x05\x06" not in content[-65536:]:
            return True
    return False


def _detect_ocr_need(content: bytes, fmt: str) -> str:
    """Heuristic: check if PDF is image-only (needs OCR)."""
    if fmt != "PDF":
        return "NOT_NEEDED"
    # Quick check: look for text operators in PDF content streams
    text_ops = [b"BT", b"Tj", b"TJ", b"'", b'"']
    for op in text_ops:
        if op in content:
            return "NOT_NEEDED"
    # No text operators found — likely image-only
    return "NEEDED"


def _estimate_page_count(content: bytes, fmt: str) -> int:
    """Estimate page count from file structure.

    For PDF: count /Type /Page (or /Pages with Count)
    For DOCX: rough estimate from file size
    """
    if fmt == "PDF":
        import re

        # Count /Type /Page occurrences (exclude /Parent, /Pages)
        pages = len(re.findall(rb"/Type\s*/Page[^s]", content))
        if pages > 0:
            return pages
        # Fallback: try /Count in /Pages dictionary
        count_match = re.search(rb"/Count\s+(\d+)", content)
        if count_match:
            return int(count_match.group(1))
    # Rough fallback: ~30KB per page
    return max(1, len(content) // 30720)
