"""
4-Layer Constraint Validators.

Aligned with langchain_hitl_arch-v1.0.md §VII 上游约束对齐验证:
  Layer 1 — Graph/Node:  IP-1 non-skippable enforcement
  Layer 2 — API/HTTP:    Pre-submit high-risk completion gate
  Layer 3 — StateMachine: 9-state lifecycle transition validity
  Layer 4 — Audit:       Immutable chain-hash logging

Each layer is a gate; a violation raises ``ConstraintViolationError``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .types import DocumentStatus


# ──────────────────────────────────────────────
# Error type
# ──────────────────────────────────────────────


class ConstraintViolationError(Exception):
    """Raised when a 4-layer constraint is violated."""

    def __init__(self, layer: int, message: str) -> None:
        self.layer = layer
        self.message = message
        super().__init__(f"[Layer {layer}] {message}")


# ──────────────────────────────────────────────
# Limit constants (business_model.md + boundary_spec)
# ──────────────────────────────────────────────

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_PAGE_COUNT = 200
ALLOWED_FORMATS = ("PDF", "DOCX")
REJECT_REASON_MIN_LENGTH = 10
COMMENT_MIN_LENGTH = 10


# ──────────────────────────────────────────────
# Layer 1 — Graph / Node
# ──────────────────────────────────────────────


def enforce_ip1_non_skippable(
    *,
    pending_interrupts: list[str],
    interrupt_sessions: dict[str, Any],
) -> None:
    """Layer 1: Enforce that IP-1 cannot be bypassed.

    Rule:
        If any IP-1 interrupt is ``WAITING``, the graph MUST NOT proceed
        past the ``human_review`` node.  All IP-1 interrupts must be
        ``RESOLVED`` before the graph can advance to ``finalize_report``.

    Args:
        pending_interrupts: List of interrupt IDs registered on the state.
        interrupt_sessions: Dict of ``interrupt_id → InterruptSession``.

    Raises:
        ConstraintViolationError: If an IP-1 interrupt is still waiting.
    """
    for ip_id in pending_interrupts:
        session = interrupt_sessions.get(ip_id)
        if session is None:
            continue
        if (
            session.interrupt_point == "IP-1"
            and session.status == "waiting"
        ):
            raise ConstraintViolationError(
                layer=1,
                message=(
                    f"IP-1 interrupt {ip_id} is still WAITING. "
                    "HIGH-risk clauses require mandatory human review "
                    "before the workflow can proceed."
                ),
            )


def enforce_interrupt_order(
    *,
    current_point: str,
    resolved_points: set[str],
) -> None:
    """Layer 1: Enforce interrupt sequencing.

    IP-1 must be resolved before IP-2 can be surfaced.
    IP-2 must be resolved before IP-3 can be surfaced.

    Args:
        current_point: The interrupt point being entered.
        resolved_points: Set of already-resolved interrupt point types.

    Raises:
        ConstraintViolationError: If ordering is violated.
    """
    order = {"IP-1": 0, "IP-2": 1, "IP-3": 2}
    current_ord = order.get(current_point, -1)

    for pt, ord_ in order.items():
        if ord_ < current_ord and pt not in resolved_points:
            raise ConstraintViolationError(
                layer=1,
                message=(
                    f"Cannot enter {current_point} before {pt} is resolved."
                ),
            )


# ──────────────────────────────────────────────
# Layer 2 — API / HTTP
# ──────────────────────────────────────────────


def enforce_high_risk_completion(
    *,
    total_high_risk: int,
    approved_high_risk: int,
    pending_high_risk_interrupts: int,
) -> Optional[str]:
    """Layer 2: Enforce all HIGH-risk items are resolved before submit.

    Called by ``handle_final_submit()``. Returns an error message
    if the constraint fails, or ``None`` if it passes.

    Args:
        total_high_risk: Total HIGH-risk flags for the document.
        approved_high_risk: Count of resolved (approved/amended/rejected) HIGH flags.
        pending_high_risk_interrupts: Count of still-WAITING IP-1 interrupts.

    Returns:
        Error message string, or ``None`` if all HIGH risks are resolved.
    """
    unresolved = total_high_risk - approved_high_risk
    if unresolved > 0 or pending_high_risk_interrupts > 0:
        remaining = max(unresolved, pending_high_risk_interrupts)
        return f"仍有 {remaining} 项高风险条款待审批"
    return None


def enforce_escalate_target_level(target_level: str) -> None:
    """Layer 2: Escalate must target HIGH only."""
    if target_level != "HIGH":
        raise ConstraintViolationError(
            layer=2,
            message=f"Escalate target level must be HIGH, got {target_level}.",
        )


# ──────────────────────────────────────────────
# Layer 3 — StateMachine
# ──────────────────────────────────────────────


# Valid transition map: from_status → set of allowed to_status
_VALID_TRANSITIONS: dict[str, set[str]] = {
    DocumentStatus.CREATED: {
        DocumentStatus.UPLOADED,
        DocumentStatus.CANCELLED,
    },
    DocumentStatus.UPLOADED: {
        DocumentStatus.PARSING,
        DocumentStatus.CANCELLED,
    },
    DocumentStatus.PARSING: {
        DocumentStatus.PARSED,
        DocumentStatus.FAILED,
        DocumentStatus.CANCELLED,
    },
    DocumentStatus.PARSED: {
        DocumentStatus.REVIEWING,
        DocumentStatus.CANCELLED,
    },
    DocumentStatus.REVIEWING: {
        DocumentStatus.REVIEWED,
        DocumentStatus.FAILED,
        DocumentStatus.CANCELLED,
    },
    DocumentStatus.REVIEWED: {
        DocumentStatus.HUMAN_REVIEW,
        DocumentStatus.CANCELLED,
    },
    DocumentStatus.HUMAN_REVIEW: {
        DocumentStatus.COMPLETED,
        DocumentStatus.REVIEWING,  # back_to_review
        DocumentStatus.CANCELLED,
    },
    DocumentStatus.COMPLETED: set(),  # terminal
    DocumentStatus.FAILED: {
        DocumentStatus.PARSING,  # retry parse
        DocumentStatus.REVIEWING,  # retry review
        DocumentStatus.CANCELLED,
    },
    DocumentStatus.CANCELLED: set(),  # terminal
}


def validate_status_transition(
    from_status: str,
    to_status: str,
) -> bool:
    """Layer 3: Validate a status transition follows the 9-state lifecycle.

    Args:
        from_status: Current document status.
        to_status: Proposed next status.

    Returns:
        ``True`` if the transition is valid.

    Raises:
        ConstraintViolationError: If the transition is not allowed.
    """
    allowed = _VALID_TRANSITIONS.get(from_status)
    if allowed is None:
        raise ConstraintViolationError(
            layer=3,
            message=f"Unknown from_status: {from_status}.",
        )
    if to_status not in allowed:
        raise ConstraintViolationError(
            layer=3,
            message=(
                f"Invalid status transition: "
                f"{from_status} → {to_status}. "
                f"Allowed: {sorted(allowed)}."
            ),
        )
    return True


# ──────────────────────────────────────────────
# Layer 4 — Audit / Immutable
# ──────────────────────────────────────────────


@dataclass
class AuditLogEntry:
    """A single entry in the audit log chain.

    Uses SHA-256 chain-hashing for tamper evidence (data_model_spec §3.3).
    """

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    operation_type: str = ""  # 26-enum from data model
    user_id: str = ""
    agent_name: str = ""
    document_id: str = ""
    clause_id: str = ""
    risk_flag_id: str = ""
    decision_id: str = ""
    before_snapshot: Optional[dict[str, Any]] = None
    after_snapshot: Optional[dict[str, Any]] = None

    # Chain-hash fields
    prev_hash: str = ""
    current_hash: str = ""

    def compute_hash(self) -> str:
        """Compute the SHA-256 hash of this entry's content.

        Uses prev_hash + operation_type + timestamp + entity IDs
        to create a tamper-evident chain.
        """
        content = (
            f"{self.prev_hash}|{self.operation_type}|"
            f"{self.timestamp.isoformat()}|{self.user_id}|"
            f"{self.document_id}|{self.clause_id}|"
            f"{self.risk_flag_id}|{self.decision_id}"
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def seal(self, prev_hash: str) -> None:
        """Link this entry to the previous one and seal the hash."""
        self.prev_hash = prev_hash
        self.current_hash = self.compute_hash()


class ImmutableAuditLog:
    """Append-only audit log with chain-hash integrity.

    Every write computes ``current_hash = SHA-256(prev_hash || entry_data)``.
    No deletion or modification is supported after write (Layer 4).
    """

    def __init__(self) -> None:
        self._entries: list[AuditLogEntry] = []
        self._last_hash: str = "0" * 64  # genesis hash

    def append(self, entry: AuditLogEntry) -> AuditLogEntry:
        """Append an entry to the log and seal it with the chain hash.

        Args:
            entry: The audit entry to record.

        Returns:
            The sealed entry (mutated in-place).
        """
        prev = self._entries[-1].current_hash if self._entries else self._last_hash
        entry.seal(prev)
        self._entries.append(entry)
        return entry

    def verify_integrity(self) -> bool:
        """Verify the entire chain is intact.

        Returns:
            ``True`` if every entry's ``current_hash`` matches the
            recalculated hash from its predecessor.
        """
        expected_prev = self._last_hash
        for entry in self._entries:
            # Recompute what current_hash should be given prev_hash
            entry.prev_hash = expected_prev
            recomputed = entry.compute_hash()
            if recomputed != entry.current_hash:
                return False
            expected_prev = entry.current_hash
        return True

    @property
    def entries(self) -> list[AuditLogEntry]:
        """Return all entries (read-only view)."""
        return list(self._entries)

    @property
    def count(self) -> int:
        """Number of entries in the log."""
        return len(self._entries)


def log_immutable_decision(
    audit_log: ImmutableAuditLog,
    *,
    operation_type: str,
    user_id: str,
    document_id: str,
    clause_id: str = "",
    risk_flag_id: str = "",
    decision_id: str = "",
    agent_name: str = "",
    before_snapshot: Optional[dict[str, Any]] = None,
    after_snapshot: Optional[dict[str, Any]] = None,
) -> AuditLogEntry:
    """Layer 4: Log a human decision immutably.

    Every call creates and appends a sealed ``AuditLogEntry`` to the
    append-only chain.  This is the **only** way to write audit data.

    Args:
        audit_log: The ``ImmutableAuditLog`` instance to append to.
        operation_type: One of the 26 ``AuditLog.operation_type`` enum values.
        user_id: ID of the human reviewer.
        document_id: Owning document ID.
        clause_id: Related clause ID (optional).
        risk_flag_id: Related risk flag ID (optional).
        decision_id: Related decision ID (optional).
        agent_name: Name of the AI agent involved (optional).
        before_snapshot: State snapshot before the decision (optional).
        after_snapshot: State snapshot after the decision (optional).

    Returns:
        The sealed ``AuditLogEntry``.
    """
    entry = AuditLogEntry(
        operation_type=operation_type,
        user_id=user_id,
        agent_name=agent_name,
        document_id=document_id,
        clause_id=clause_id,
        risk_flag_id=risk_flag_id,
        decision_id=decision_id,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
    )
    return audit_log.append(entry)
