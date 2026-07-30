"""
3 InterruptPoint Implementations.

Aligned with langchain_hitl_arch-v1.0.md §5:
  - IP-1: HIGH risk   → non-skippable, individual approval
  - IP-2: MEDIUM risk → batch-skippable, bulk confirmation
  - IP-3: FINAL conf  → non-skippable, final submit gate

Each function calls ``langgraph.types.interrupt()`` within the
``human_review`` node of the 7-node StateGraph.
"""

from __future__ import annotations

from typing import Any, Optional

from langgraph.types import interrupt

from .types import (
    IP1Payload,
    IP2BatchItem,
    IP2Payload,
    IP3Payload,
    IP3RiskSummary,
)


# ──────────────────────────────────────────────
# IP-1: HIGH risk — individual, non-skippable
# ──────────────────────────────────────────────

def ip1_high_risk(
    *,
    clause_id: str,
    risk_level: str,
    risk_category: str,
    ai_confidence: float,
    playbook_diff: str,
    suggestion: str,
    original_text: str,
    clause_location: dict[str, Any],
    rationale_text: str = "",
    regulation_reference: str = "",
    interrupt_id: str | None = None,
) -> dict[str, Any]:
    """🔴 IP-1: Pause for human decision on a HIGH-risk clause.

    **Non-skippable.**  The graph will *not* proceed past this interrupt
    until the human reviewer explicitly calls one of:
      - ``POST /risk-flags/{id}/approve``  → ``"decision": "approve"``
      - ``POST /risk-flags/{id}/edit``     → ``"decision": "edit"``
      - ``POST /risk-flags/{id}/reject``   → ``"decision": "reject"``

    Args:
        clause_id: Unique clause identifier.
        risk_level: Must be ``"HIGH"``.
        risk_category: e.g. ``"合规风险"``, ``"财务风险"``.
        ai_confidence: AI confidence score 0.0–1.0.
        playbook_diff: Diff text between playbook standard and actual clause.
        suggestion: AI-suggested rewording.
        original_text: Actual clause text from the source document.
        clause_location: ``ClauseLocationDict`` with page/offset info.
        rationale_text: Explainability text from the AI agent.
        regulation_reference: Relevant regulation citation.
        interrupt_id: Optional pre-generated ID; auto-generated if omitted.

    Returns:
        The human decision dict returned by ``interrupt()`` when resumed.
    """
    payload: IP1Payload = {
        "interrupt_id": interrupt_id or _gen_interrupt_id("IP-1", clause_id),
        "interrupt_type": "IP-1",
        "clause_id": clause_id,
        "risk_level": risk_level,
        "risk_category": risk_category,
        "ai_confidence": ai_confidence,
        "playbook_diff": playbook_diff,
        "suggestion": suggestion,
        "original_text": original_text,
        "clause_location": clause_location,
        "rationale_text": rationale_text,
        "regulation_reference": regulation_reference,
    }
    # interrupt() raises GraphInterrupt; on resume returns the human's
    # decision dict (e.g. {"decision": "approve", "comment": "..."})
    decision: dict[str, Any] = interrupt(payload)
    return decision


# ──────────────────────────────────────────────
# IP-2: MEDIUM risk — batch, skippable
# ──────────────────────────────────────────────

def ip2_medium_risk(
    *,
    items: list[IP2BatchItem],
    interrupt_id: str | None = None,
) -> dict[str, Any]:
    """🟡 IP-2: Pause for human batch-review of MEDIUM-risk clauses.

    **Batch-skippable.**  The human reviewer can:
      - ``POST /risk-flags/batch-approve`` → ``"type": "batch_confirm"``
        (auto-pass all items, graph continues immediately)
      - ``POST /risk-flags/sample`` → ``"type": "deep_dive"``
        (spot-check a deterministic sample before passing)

    Args:
        items: List of ``IP2BatchItem`` dicts, one per medium-risk clause.
        interrupt_id: Optional pre-generated ID.

    Returns:
        The human batch decision dict returned by ``interrupt()``.
    """
    payload: IP2Payload = {
        "interrupt_id": interrupt_id or _gen_interrupt_id("IP-2", f"batch_{len(items)}"),
        "interrupt_type": "IP-2",
        "items": items,
        "total_count": len(items),
    }
    decision: dict[str, Any] = interrupt(payload)
    return decision


# ──────────────────────────────────────────────
# IP-3: FINAL confirmation — non-skippable
# ──────────────────────────────────────────────

def ip3_final_confirm(
    *,
    high_risk_summary: IP3RiskSummary,
    medium_risk_summary: IP3RiskSummary,
    low_risk_summary: IP3RiskSummary,
    manual_additions: int = 0,
    audit_summary: str = "",
    interrupt_id: str | None = None,
) -> dict[str, Any]:
    """🔵 IP-3: Pause for final human confirmation before report generation.

    **Non-skippable.**  The human reviewer must explicitly:
      - ``POST /documents/{id}/submit``      → ``"action": "confirm_submit"``
      - ``POST /documents/{id}/save-draft``  → ``"action": "save_draft"``
      - ``"action": "back_to_review"``       → return to manual review

    The API layer enforces ``all_high_risk_resolved == True`` before
    ``confirm_submit`` is accepted (4-layer constraint #2).

    Args:
        high_risk_summary: Aggregated HIGH risk statistics.
        medium_risk_summary: Aggregated MEDIUM risk statistics.
        low_risk_summary: Aggregated LOW risk statistics.
        manual_additions: Count of manually-added risk flags.
        audit_summary: Human-readable audit trail summary.
        interrupt_id: Optional pre-generated ID.

    Returns:
        The human final-decision dict.
    """
    payload: IP3Payload = {
        "interrupt_id": interrupt_id or _gen_interrupt_id("IP-3", "final"),
        "interrupt_type": "IP-3",
        "high_risk_summary": high_risk_summary,
        "medium_risk_summary": medium_risk_summary,
        "low_risk_summary": low_risk_summary,
        "manual_additions": manual_additions,
        "audit_summary": audit_summary,
    }
    decision: dict[str, Any] = interrupt(payload)
    return decision


# ──────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────

def _gen_interrupt_id(ip_type: str, entity_id: str) -> str:
    """Generate a deterministic-but-unique interrupt ID."""
    import uuid

    return f"ip_{ip_type.lower().replace('-', '')}_{entity_id[:8]}_{uuid.uuid4().hex[:8]}"
