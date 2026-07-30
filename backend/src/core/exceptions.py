"""Unified application exception hierarchy.

All service-layer errors are raised as AppException subclasses.
A single FastAPI exception_handler converts them to the standard
API response envelope: {"code": ..., "message": ..., "data": null, "request_id": ...}
"""

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    """Machine-readable error codes matching the API spec §2.3."""

    INVALID_PARAMS = "INVALID_PARAMS"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # ── Domain-specific ───────────────────────────────────────────
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    FILE_ENCRYPTED = "FILE_ENCRYPTED"
    FILE_CORRUPTED = "FILE_CORRUPTED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    PAGE_LIMIT_EXCEEDED = "PAGE_LIMIT_EXCEEDED"


HTTP_STATUS_MAP: dict[ErrorCode, int] = {
    ErrorCode.INVALID_PARAMS: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.VALIDATION_FAILED: 422,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.UNSUPPORTED_FORMAT: 422,
    ErrorCode.FILE_ENCRYPTED: 422,
    ErrorCode.FILE_CORRUPTED: 422,
    ErrorCode.FILE_TOO_LARGE: 422,
    ErrorCode.PAGE_LIMIT_EXCEEDED: 422,
}


class AppException(Exception):
    """Base for all application exceptions.

    Every instance maps to an HTTP status code via ErrorCode.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str = "",
        detail: str | None = None,
    ) -> None:
        self.code = code
        self.message = message or code.value
        self.detail = detail
        super().__init__(self.message)

    @property
    def http_status(self) -> int:
        return HTTP_STATUS_MAP.get(self.code, 500)


# ── Convenience subclasses ────────────────────────────────────────────


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            code=ErrorCode.NOT_FOUND,
            message=f"{resource} not found: {identifier}",
        )


class ConflictError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(code=ErrorCode.CONFLICT, message=message)


class ValidationError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(code=ErrorCode.VALIDATION_FAILED, message=message)


class FileValidationError(AppException):
    """Raised by the 5-layer file validation chain."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(code=code, message=message)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(code=ErrorCode.FORBIDDEN, message=message)
