"""
Command(resume) Handlers — 8 Frontend Operations.

Aligned with:
- langchain_hitl_arch-v1.0.md §5.1 (8 operation → Command mapping)
- api_spec-v1.0.md §5 (Human Review API Group, endpoints 18–27)

Each handler:
  1. Validates business rules (e.g. reject_reason >= 10 chars).
  2. Constructs the correct ``Command(resume=...)`` payload.
  3. Returns a result dict appropriate for the HTTP response.

Operations that go through ``interrupt()`` resume:
  1. approve          → IP-1
  2. edit             → IP-1
  3. reject           → IP-1
  4. batch_approve    → IP-2
  5. spot_check       → IP-2
  6. escalate         → IP-1 / IP-2
  7. manual_add       → NO interrupt (direct state write per spec §5.7)
  8. final_submit     → IP-3
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from langgraph.types import Command


# ──────────────────────────────────────────────
# Response dataclass
# ──────────────────────────────────────────────


@dataclass
class HandlerResult:
    """Unified result from a command handler.

    Attributes:
        success: Whether the operation was accepted.
        command: The ``Command`` to pass to ``graph.stream()`` for resume,
            or ``None`` if no interrupt resume is needed (manual_add).
        data: Payload for the HTTP response body.
        error_code: Error code string if ``success == False``.
        http_status: Suggested HTTP status code.
    """

    success: bool
    command: Optional[Command] = None
    data: dict[str, Any] = field(default_factory=dict)
    error_code: str = ""
    http_status: int = 200


# ──────────────────────────────────────────────
# Type aliases
# ──────────────────────────────────────────────

# Callback invoked after DB writes and before returning the response record
AfterWriteCallback = Callable[[dict[str, Any]], None]

# Database-write function signature (would be injected in production)
DbWriter = Callable[..., dict[str, Any]]


# ──────────────────────────────────────────────
# 1. approve — POST /risk-flags/{id}/approve
# ──────────────────────────────────────────────


def handle_approve(
    *,
    risk_flag_id: str,
    comment: str = "",
    reviewer_id: str = "",
    db_writer: Optional[DbWriter] = None,
) -> HandlerResult:
    """Handle IP-1 ``approve`` operation.

    Backend processing (api_spec §5.1):
      1. Update RiskFlag.status → CONFIRMED
      2. Write ReviewDecision (decision_type=APPROVE)
      3. Write AuditLog (operation_type=HUMAN_APPROVE)
      4. Resume via Command(resume={"decision": "approve"})

    Args:
        risk_flag_id: The risk flag being approved.
        comment: Optional reviewer comment.
        reviewer_id: ID of the human reviewer.
        db_writer: Optional DB-write hook (injected).

    Returns:
        ``HandlerResult`` with resume Command.
    """
    if db_writer:
        db_writer({
            "risk_flag_id": risk_flag_id,
            "new_status": "CONFIRMED",
            "decision_type": "APPROVE",
            "reviewer_id": reviewer_id,
            "comment": comment,
            "audit_type": "HUMAN_APPROVE",
        })

    return HandlerResult(
        success=True,
        command=Command(resume={"decision": "approve", "comment": comment}),
        data={
            "risk_flag_id": risk_flag_id,
            "status": "CONFIRMED",
            "message": "Risk assessment confirmed.",
        },
    )


# ──────────────────────────────────────────────
# 2. edit — POST /risk-flags/{id}/edit
# ──────────────────────────────────────────────


def handle_edit(
    *,
    risk_flag_id: str,
    comment: str,
    reviewer_id: str = "",
    modified_risk_level: str = "",
    modified_risk_category: str = "",
    modified_suggestion: str = "",
    db_writer: Optional[DbWriter] = None,
) -> HandlerResult:
    """Handle IP-1 ``edit`` operation.

    Validation (api_spec §5.2):
      - ``comment`` is **required** and must be >= 10 characters.
      - HIGH → MEDIUM: allowed.
      - HIGH → LOW: allowed (must justify in comment).
      - MEDIUM → HIGH: use ``escalate`` instead.

    Backend processing:
      1. Update RiskFlag.status → AMENDED
      2. Save modified fields
      3. Write ReviewDecision (decision_type=EDIT)
      4. Write AuditLog (operation_type=HUMAN_EDIT)
      5. Resume via Command(resume={"decision": "edit", "modified_fields": {...}})

    Args:
        risk_flag_id: The risk flag being edited.
        comment: **Required.** Reason for modification (>= 10 chars).
        reviewer_id: ID of the human reviewer.
        modified_risk_level: New risk level (None = unchanged).
        modified_risk_category: New risk category (None = unchanged).
        modified_suggestion: New suggested wording (None = unchanged).
        db_writer: Optional DB-write hook (injected).

    Returns:
        ``HandlerResult`` with resume Command, or error if comment too short.
    """
    # --- validation ---
    if len(comment.strip()) < 10:
        return HandlerResult(
            success=False,
            error_code="VALIDATION_FAILED",
            http_status=422,
            data={"message": "Comment must be at least 10 characters."},
        )

    if modified_risk_level == "HIGH":
        return HandlerResult(
            success=False,
            error_code="VALIDATION_FAILED",
            http_status=422,
            data={
                "message": (
                    "Upgrading to HIGH is not allowed via edit. "
                    "Use POST /risk-flags/{id}/escalate instead."
                ),
            },
        )

    modified_fields: dict[str, str] = {}
    if modified_risk_level:
        modified_fields["risk_level"] = modified_risk_level
    if modified_risk_category:
        modified_fields["risk_category"] = modified_risk_category
    if modified_suggestion:
        modified_fields["suggested_wording"] = modified_suggestion

    if db_writer:
        db_writer({
            "risk_flag_id": risk_flag_id,
            "new_status": "AMENDED",
            "decision_type": "EDIT",
            "reviewer_id": reviewer_id,
            "comment": comment,
            "modified_fields": modified_fields,
            "audit_type": "HUMAN_EDIT",
        })

    return HandlerResult(
        success=True,
        command=Command(
            resume={
                "decision": "edit",
                "comment": comment,
                "modified_fields": modified_fields,
            }
        ),
        data={
            "risk_flag_id": risk_flag_id,
            "status": "AMENDED",
        },
    )


# ──────────────────────────────────────────────
# 3. reject — POST /risk-flags/{id}/reject
# ──────────────────────────────────────────────


def handle_reject(
    *,
    risk_flag_id: str,
    reject_reason: str,
    reviewer_id: str = "",
    db_writer: Optional[DbWriter] = None,
) -> HandlerResult:
    """Handle IP-1 ``reject`` operation.

    Validation (api_spec §5.3):
      - ``reject_reason`` is **required** and must be >= 10 characters.
      - < 10 chars → 422 VALIDATION_FAILED.

    Backend processing:
      1. Update RiskFlag.status → REJECTED
      2. Write ReviewDecision (decision_type=REJECT)
      3. Write AuditLog (operation_type=HUMAN_REJECT)
      4. Resume via Command(resume={"decision": "reject", "comment": str})

    Args:
        risk_flag_id: The risk flag being rejected.
        reject_reason: **Required.** Detailed reason (>= 10 chars).
        reviewer_id: ID of the human reviewer.
        db_writer: Optional DB-write hook (injected).

    Returns:
        ``HandlerResult`` with resume Command, or error if reason too short.
    """
    # --- validation ---
    if len(reject_reason.strip()) < 10:
        return HandlerResult(
            success=False,
            error_code="VALIDATION_FAILED",
            http_status=422,
            data={"message": "Reject reason must be at least 10 characters."},
        )

    if db_writer:
        db_writer({
            "risk_flag_id": risk_flag_id,
            "new_status": "REJECTED",
            "decision_type": "REJECT",
            "reviewer_id": reviewer_id,
            "comment": reject_reason,
            "audit_type": "HUMAN_REJECT",
        })

    return HandlerResult(
        success=True,
        command=Command(
            resume={"decision": "reject", "comment": reject_reason}
        ),
        data={
            "risk_flag_id": risk_flag_id,
            "status": "REJECTED",
            "message": "Risk assessment has been dismissed.",
        },
    )


# ──────────────────────────────────────────────
# 4. batch_approve — POST /risk-flags/batch-approve
# ──────────────────────────────────────────────


def handle_batch_approve(
    *,
    document_id: str,
    risk_flag_ids: list[str],
    reviewer_id: str = "",
    db_writer: Optional[DbWriter] = None,
) -> HandlerResult:
    """Handle IP-2 ``batch_approve`` operation.

    Backend processing (api_spec §5.4):
      1. Batch-update all MEDIUM RiskFlag.status → UNREVIEWED_AUTO_PASSED
      2. Write 1 ReviewDecision (decision_type=BATCH_CONFIRM, contains all IDs)
      3. Write AuditLog (operation_type=BATCH_CONFIRM)
      4. Resume via Command(resume={"type": "batch_confirm", "items": [...]})

    Args:
        document_id: Owning document.
        risk_flag_ids: List of MEDIUM-risk flag IDs to auto-pass.
        reviewer_id: ID of the human reviewer.
        db_writer: Optional DB-write hook (injected).

    Returns:
        ``HandlerResult`` with batch resume Command.
    """
    if not risk_flag_ids:
        return HandlerResult(
            success=False,
            error_code="INVALID_PARAMS",
            http_status=400,
            data={"message": "At least one risk_flag_id is required."},
        )

    items: list[dict[str, str]] = [
        {"risk_flag_id": fid, "decision": "auto_pass"} for fid in risk_flag_ids
    ]

    if db_writer:
        db_writer({
            "document_id": document_id,
            "risk_flag_ids": risk_flag_ids,
            "new_status": "UNREVIEWED_AUTO_PASSED",
            "decision_type": "BATCH_CONFIRM",
            "reviewer_id": reviewer_id,
            "audit_type": "BATCH_CONFIRM",
        })

    return HandlerResult(
        success=True,
        command=Command(resume={"type": "batch_confirm", "items": items}),
        data={
            "batch_approved_count": len(risk_flag_ids),
        },
    )


# ──────────────────────────────────────────────
# 5. spot_check — POST /risk-flags/sample
# ──────────────────────────────────────────────


def handle_spot_check(
    *,
    document_id: str,
    reviewer_id: str = "",
    sample_ratio: float = 0.11,
    low_risk_pool: Optional[list[dict[str, Any]]] = None,
    db_writer: Optional[DbWriter] = None,
) -> HandlerResult:
    """Handle IP-2 ``spot_check`` (deep_dive) operation.

    Uses a **deterministic seed** (document_id + reviewer_id) to sample
    ``sample_ratio`` fraction of LOW-risk flags for human spot-audit
    (api_spec §5.5).

    Args:
        document_id: Owning document.
        reviewer_id: ID of the human reviewer (used in seed).
        sample_ratio: Fraction of LOW-risk flags to sample (default 0.11).
        low_risk_pool: Pre-fetched list of LOW-risk RiskFlag dicts.
            If ``None``, sampling returns an empty result.
        db_writer: Optional DB-write hook (injected).

    Returns:
        ``HandlerResult`` with sampled items.
    """
    if low_risk_pool is None:
        low_risk_pool = []

    # Deterministic seed per spec §5.5: sha256(doc_id + user_id)[:8]
    seed_str = f"{document_id}_{reviewer_id}"
    seed_bytes = hashlib.sha256(seed_str.encode()).digest()[:8]
    seed = int.from_bytes(seed_bytes, "big")
    rng = random.Random(seed)

    sample_size = max(1, int(len(low_risk_pool) * sample_ratio))
    sampled = rng.sample(low_risk_pool, min(sample_size, len(low_risk_pool)))

    sampled_ids = [f["risk_flag_id"] for f in sampled]

    if db_writer:
        db_writer({
            "risk_flag_ids": sampled_ids,
            "new_status": "UNDER_SPOT_CHECK",
            "decision_type": "BATCH_CONFIRM",  # initiated via deep_dive
            "reviewer_id": reviewer_id,
            "audit_type": "SPOT_CHECK_SAMPLE",
            "seed_info": seed_bytes.hex(),
        })

    return HandlerResult(
        success=True,
        command=Command(
            resume={
                "type": "deep_dive",
                "items": [
                    {"risk_flag_id": rid, "decision": "sample_review"}
                    for rid in sampled_ids
                ],
            }
        ),
        data={
            "sampled_risk_flags": sampled,
            "sample_size": len(sampled),
            "total_low_risk": len(low_risk_pool),
            "seed_info": f"sha256({document_id}_{reviewer_id})[:8]",
        },
    )


# ──────────────────────────────────────────────
# 6. escalate — POST /risk-flags/{id}/escalate
# ──────────────────────────────────────────────


def handle_escalate(
    *,
    risk_flag_id: str,
    new_level: str = "HIGH",
    reason: str = "",
    reviewer_id: str = "",
    db_writer: Optional[DbWriter] = None,
) -> HandlerResult:
    """Handle ``escalate`` operation (IP-1 or IP-2).

    Backend processing (api_spec §5.6):
      1. Update RiskFlag.risk_level → HIGH (**irreversible**)
      2. Update RiskFlag.status → ESCALATED_TO_HIGH
      3. Add to HIGH-risk approval queue
      4. Write ReviewDecision (decision_type=ESCALATE)
      5. Write AuditLog (operation_type=SPOT_CHECK_ESCALATE)

    Args:
        risk_flag_id: The risk flag being escalated.
        new_level: Target level (must be "HIGH").
        reason: Human justification for escalation.
        reviewer_id: ID of the human reviewer.
        db_writer: Optional DB-write hook (injected).

    Returns:
        ``HandlerResult`` with resume Command.
    """
    if new_level != "HIGH":
        return HandlerResult(
            success=False,
            error_code="VALIDATION_FAILED",
            http_status=422,
            data={"message": "Escalate target level must be HIGH."},
        )

    if db_writer:
        db_writer({
            "risk_flag_id": risk_flag_id,
            "new_level": new_level,
            "new_status": "ESCALATED_TO_HIGH",
            "decision_type": "ESCALATE",
            "reviewer_id": reviewer_id,
            "reason": reason,
            "audit_type": "SPOT_CHECK_ESCALATE",
        })

    return HandlerResult(
        success=True,
        command=Command(
            resume={"decision": "escalate", "new_level": new_level}
        ),
        data={
            "risk_flag_id": risk_flag_id,
            "new_level": "HIGH",
            "status": "ESCALATED_TO_HIGH",
            "message": "Escalated to HIGH-risk; mandatory human review required.",
        },
    )


# ──────────────────────────────────────────────
# 7. manual_add — POST /risk-flags/manual
# ──────────────────────────────────────────────


def handle_manual_add(
    *,
    document_id: str,
    clause_location: dict[str, Any],
    risk_level: str,
    risk_category: str,
    description: str,
    clause_text: str = "",
    reviewer_id: str = "",
    db_writer: Optional[DbWriter] = None,
) -> HandlerResult:
    """Handle ``manual_add`` operation.

    **Does NOT go through interrupt.**  Writes directly to state
    (api_spec §5.7, langchain_hitl_arch-v1.0.md §5.1 row 7).

    Backend processing:
      1. Create RiskFlag (source=MANUALLY_ADDED, status=PENDING_REVIEW)
      2. Create Clause (source=MANUAL)
      3. Write ReviewDecision (decision_type=MANUAL_ADD)
      4. Write AuditLog (operation_type=MANUAL_ADD)
      5. Add to HIGH-risk approval queue

    Args:
        document_id: Owning document.
        clause_location: ClauseLocation dict with page/offset info.
        risk_level: Manual risk level (HIGH/MEDIUM/LOW).
        risk_category: Manual risk category.
        description: Human description (>= 10 chars required).
        clause_text: Selected text from the source document.
        reviewer_id: ID of the human reviewer.
        db_writer: Optional DB-write hook (injected).

    Returns:
        ``HandlerResult`` with **no** Command (no interrupt resume needed).
    """
    if len(description.strip()) < 10:
        return HandlerResult(
            success=False,
            error_code="VALIDATION_FAILED",
            http_status=422,
            data={"message": "Description must be at least 10 characters."},
        )

    if db_writer:
        db_writer({
            "document_id": document_id,
            "clause_location": clause_location,
            "risk_level": risk_level,
            "risk_category": risk_category,
            "description": description,
            "clause_text": clause_text,
            "reviewer_id": reviewer_id,
            "source": "MANUALLY_ADDED",
            "status": "PENDING_REVIEW",
            "decision_type": "MANUAL_ADD",
            "audit_type": "MANUAL_ADD",
        })

    return HandlerResult(
        success=True,
        command=None,  # No interrupt — direct state write
        data={
            "risk_flag_id": f"rf_{_short_uuid()}",
            "risk_level": risk_level,
            "status": "PENDING_REVIEW",
            "source": "MANUALLY_ADDED",
            "message": "Manual risk flag added to review queue.",
        },
    )


# ──────────────────────────────────────────────
# 8. final_submit — POST /documents/{id}/submit
# ──────────────────────────────────────────────


def handle_final_submit(
    *,
    document_id: str,
    comment: str = "",
    reviewer_id: str = "",
    all_high_risk_resolved: bool = False,
    db_writer: Optional[DbWriter] = None,
) -> HandlerResult:
    """Handle IP-3 ``final_submit`` operation.

    **4-layer constraint #2 (API layer):**
    ``all_high_risk_resolved`` must be ``True``; otherwise returns
    ``409 CONFLICT`` – "仍有 {N} 项高风险条款待审批" (api_spec §5.8).

    Backend processing:
      1. Update Document.status → COMPLETED
      2. Generate ReviewReport (aggregate all final states)
      3. Write AuditLog (operation_type=FINAL_SUBMIT)
      4. Resume via Command(resume={"action": "confirm_submit"})
      5. Trigger report-generation Agent for final PDF

    Args:
        document_id: The document being submitted.
        comment: Optional final comment.
        reviewer_id: ID of the human reviewer.
        all_high_risk_resolved: Must be ``True`` for submit to succeed.
        db_writer: Optional DB-write hook (injected).

    Returns:
        ``HandlerResult`` with resume Command, or 409 if high-risk unresolved.
    """
    # --- 4-layer constraint #2: API-level pre-submit gate ---
    if not all_high_risk_resolved:
        return HandlerResult(
            success=False,
            error_code="CONFLICT",
            http_status=409,
            data={
                "message": (
                    "所有高风险条款必须审批完成后才能提交。"
                    "仍有未审批的高风险项。"
                ),
            },
        )

    if db_writer:
        db_writer({
            "document_id": document_id,
            "new_status": "COMPLETED",
            "decision_type": "FINAL_SUBMIT",
            "reviewer_id": reviewer_id,
            "comment": comment,
            "audit_type": "FINAL_SUBMIT",
        })

    return HandlerResult(
        success=True,
        command=Command(resume={"action": "confirm_submit"}),
        data={
            "document_id": document_id,
            "status": "COMPLETED",
            "message": "Review submitted. Report generation in progress.",
        },
    )


# ──────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────


def _short_uuid() -> str:
    import uuid

    return uuid.uuid4().hex[:12]
