"""
InterruptSession Model & Manager.

Aligned with:
- data_model_spec-v1.0.md §3.3 (InterruptSession model, ~12 fields)
- langchain_hitl_arch-v1.0.md §6.2 (Checkpoint creation timing)

Manages the lifecycle of each interrupt event: creation → waiting → resolved.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from .types import InterruptPoint, InterruptStatus


# ──────────────────────────────────────────────
# InterruptSession model
# ──────────────────────────────────────────────


@dataclass
class InterruptSession:
    """One LangGraph interrupt event record.

    Fields match data_model_spec-v1.0.md §3.3 InterruptSession (~12 fields).
    """

    interrupt_id: str
    interrupt_point: InterruptPoint
    thread_id: str  # LangGraph thread ID
    checkpoint_id: str  # LangGraph checkpoint token
    document_id: str  # FK → Document

    # Payloads (JSON-serializable dicts)
    interrupt_payload: dict[str, Any] = field(default_factory=dict)
    resume_payload: Optional[dict[str, Any]] = None

    # Lifecycle
    status: InterruptStatus = InterruptStatus.WAITING

    # Timestamps
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    resumed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None

    # Timeout control (default: 30 minutes from creation)
    timeout_minutes: int = 30

    def __post_init__(self) -> None:
        if self.timeout_at is None:
            self.timeout_at = self.created_at + timedelta(
                minutes=self.timeout_minutes
            )

    @property
    def is_expired(self) -> bool:
        """Check if this session has exceeded its timeout window."""
        now = datetime.now(timezone.utc)
        return self.timeout_at is not None and now >= self.timeout_at

    @property
    def is_active(self) -> bool:
        """A session is active if waiting and not expired."""
        return self.status == InterruptStatus.WAITING and not self.is_expired

    def resolve(self, resume_payload: dict[str, Any]) -> None:
        """Mark this session as resolved with the human's resume data."""
        self.status = InterruptStatus.RESOLVED
        self.resume_payload = resume_payload
        self.resumed_at = datetime.now(timezone.utc)

    def expire(self) -> None:
        """Mark this session as timed out."""
        self.status = InterruptStatus.TIMEOUT
        self.resumed_at = datetime.now(timezone.utc)


# ──────────────────────────────────────────────
# InterruptSessionManager
# ──────────────────────────────────────────────


class InterruptSessionManager:
    """In-memory session store (MVP; swap with PostgreSQL in production).

    Usage::

        manager = InterruptSessionManager()
        session = manager.create(
            interrupt_point=InterruptPoint.IP1_HIGH_RISK,
            thread_id="thread_001",
            checkpoint_id="ckpt_001",
            document_id="doc_001",
            interrupt_payload=payload,
        )
        # ... human reviews ...
        manager.resolve(session.interrupt_id, resume_payload)
    """

    def __init__(self) -> None:
        self._sessions: dict[str, InterruptSession] = {}

    # ── create ────────────────────────────────

    def create(
        self,
        *,
        interrupt_point: InterruptPoint,
        thread_id: str,
        checkpoint_id: str,
        document_id: str,
        interrupt_payload: dict[str, Any],
        timeout_minutes: int = 30,
    ) -> InterruptSession:
        """Create a new interrupt session record.

        Called when an ``interrupt()`` fires inside a StateGraph node.
        """
        interrupt_id = interrupt_payload.get("interrupt_id") or _gen_id()
        session = InterruptSession(
            interrupt_id=interrupt_id,
            interrupt_point=interrupt_point,
            thread_id=thread_id,
            checkpoint_id=checkpoint_id,
            document_id=document_id,
            interrupt_payload=interrupt_payload,
            timeout_minutes=timeout_minutes,
        )
        self._sessions[session.interrupt_id] = session
        return session

    # ── resolve ───────────────────────────────

    def resolve(
        self, interrupt_id: str, resume_payload: dict[str, Any]
    ) -> Optional[InterruptSession]:
        """Mark an interrupt session as resolved.

        Returns the updated session, or ``None`` if not found.
        """
        session = self._sessions.get(interrupt_id)
        if session is None:
            return None
        session.resolve(resume_payload)
        return session

    # ── timeout ───────────────────────────────

    def expire_stale(self) -> list[InterruptSession]:
        """Expire all sessions past their timeout window.

        Returns the list of newly-expired sessions.
        """
        expired: list[InterruptSession] = []
        for session in self._sessions.values():
            if session.status == InterruptStatus.WAITING and session.is_expired:
                session.expire()
                expired.append(session)
        return expired

    def expire(self, interrupt_id: str) -> Optional[InterruptSession]:
        """Force-expire a specific session."""
        session = self._sessions.get(interrupt_id)
        if session is None:
            return None
        session.expire()
        return session

    # ── queries ───────────────────────────────

    def get(self, interrupt_id: str) -> Optional[InterruptSession]:
        """Get a session by interrupt ID."""
        return self._sessions.get(interrupt_id)

    def get_active(self) -> list[InterruptSession]:
        """Get all sessions currently in WAITING status (not expired)."""
        return [s for s in self._sessions.values() if s.is_active]

    def get_pending_for_document(
        self, document_id: str
    ) -> list[InterruptSession]:
        """Get all pending (WAITING) sessions for a given document."""
        return [
            s
            for s in self._sessions.values()
            if s.document_id == document_id
            and s.status == InterruptStatus.WAITING
        ]

    def get_pending_count_for_document(self, document_id: str) -> int:
        """Count how many interrupts are still WAITING on a document.

        Used to compute ``all_high_risk_resolved`` for API gating.
        """
        return len(self.get_pending_for_document(document_id))

    def get_by_thread(self, thread_id: str) -> list[InterruptSession]:
        """Get all sessions for a given LangGraph thread."""
        return [
            s for s in self._sessions.values() if s.thread_id == thread_id
        ]

    def has_active_interrupt(self, thread_id: str) -> bool:
        """Check if a thread has any active (waiting, not expired) interrupts."""
        return any(
            s.thread_id == thread_id and s.is_active
            for s in self._sessions.values()
        )

    # ── stats ─────────────────────────────────

    @property
    def total_sessions(self) -> int:
        """Total number of sessions tracked."""
        return len(self._sessions)


# ──────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────


def _gen_id() -> str:
    return f"is_{uuid.uuid4().hex[:16]}"
