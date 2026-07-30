"""
HITL (Human-In-The-Loop) Type Definitions.

Aligned with:
- langchain_hitl_arch-v1.0.md §4.2 (DocumentReviewState)
- langchain_hitl_arch-v1.0.md §5   (3 InterruptPoint payloads)
- api_spec-v1.0.md §5             (8 operation request/response types)
- data_model_spec-v1.0.md §3.3    (HITL interaction models)
"""

from __future__ import annotations

import operator
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional, TypedDict

from langgraph.types import Command


# ──────────────────────────────────────────────
# §4.2: DocumentReviewState (StateGraph state)
# ──────────────────────────────────────────────

class DocumentReviewState(TypedDict, total=False):
    """Core state carried through the LangGraph StateGraph.

    - ``clauses`` / ``risk_flags`` / ``review_decisions`` use Annotated reducers
      for concurrent-safe append by parallel Agent nodes.
    """

    # Document-level
    document_id: str
    doc_status: str  # 9-state lifecycle: CREATED → … → COMPLETED
    doc_metadata: dict[str, Any]  # title, type(NDA), uploaded_at

    # Clause-level (Annotated + operator.add)
    clauses: Annotated[list[dict[str, Any]], operator.add]

    # Risk-level (custom reducer merge_risk_flags)
    risk_flags: Annotated[list[dict[str, Any]], lambda a, b: _merge_risk_flags(a, b)]

    # Decision-level (append-only)
    review_decisions: Annotated[list[dict[str, Any]], operator.add]

    # Interrupt control
    interrupt_state: str  # "idle" | "waiting" | "resolved"
    pending_interrupts: list[str]  # active interrupt IDs

    # Error control
    error_info: Optional[dict[str, Any]]
    retry_count: int


def _merge_risk_flags(
    existing: list[dict[str, Any]], incoming: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Merge risk flags by agent source to deduplicate during parallel execution."""
    merged: dict[str, dict[str, Any]] = {}
    for flag in existing:
        merged[flag["id"]] = flag
    for flag in incoming:
        fid = flag.get("id", "")
        if fid not in merged:
            merged[fid] = flag
        else:
            # Update confidence / category from latest agent pass
            merged[fid].update(flag)
    return list(merged.values())


# ──────────────────────────────────────────────
# §5: Interrupt Payloads (IP-1 / IP-2 / IP-3)
# ──────────────────────────────────────────────

class ClauseLocationDict(TypedDict, total=False):
    """Position of a clause within the source document."""
    page_number: int
    paragraph_number: int
    char_offset_start: int
    char_offset_end: int
    text_hash: str


class IP1Payload(TypedDict):
    """🔴 IP-1 HIGH risk interrupt payload (non-skippable).

    Frontend renders this as an approval card on P5.
    """

    interrupt_id: str
    interrupt_type: str  # "IP-1"
    clause_id: str
    risk_level: str  # "HIGH"
    risk_category: str  # e.g. "合规风险"
    ai_confidence: float  # 0.0-1.0
    playbook_diff: str  # diff text between standard and actual clause
    suggestion: str  # AI-suggested wording
    original_text: str  # actual clause text
    clause_location: ClauseLocationDict
    rationale_text: str  # explainability field
    regulation_reference: str  # relevant regulation citation


class IP2BatchItem(TypedDict):
    """Single item within an IP-2 batch payload."""
    clause_id: str
    risk_category: str
    ai_confidence: float
    clause_summary: str


class IP2Payload(TypedDict):
    """🟡 IP-2 MEDIUM risk interrupt payload (batch-skippable).

    Frontend renders this as a batch approval panel.
    """

    interrupt_id: str
    interrupt_type: str  # "IP-2"
    items: list[IP2BatchItem]
    total_count: int


class IP3RiskSummary(TypedDict):
    """Aggregated risk summary per level."""
    count: int
    confirmed: int
    amended: int
    rejected: int
    auto_passed: int


class IP3Payload(TypedDict):
    """🔵 IP-3 FINAL confirmation interrupt payload (non-skippable).

    Frontend renders this as the final submit confirmation page.
    """

    interrupt_id: str
    interrupt_type: str  # "IP-3"
    high_risk_summary: IP3RiskSummary
    medium_risk_summary: IP3RiskSummary
    low_risk_summary: IP3RiskSummary
    manual_additions: int
    audit_summary: str  # human-readable audit trail summary


# ──────────────────────────────────────────────
# §5.1: Resume Payloads (8 frontend operations)
# ──────────────────────────────────────────────

class IP1ResumeDecision(TypedDict, total=False):
    """Resume payload for IP-1 approve / edit / reject."""
    decision: str  # "approve" | "edit" | "reject"
    comment: str
    modified_fields: dict[str, Any]  # only for "edit"
    reject_reason: str  # only for "reject"; >= 10 chars


class IP2ResumeDecision(TypedDict):
    """Resume payload for IP-2 batch_confirm / deep_dive."""
    type: str  # "batch_confirm" | "deep_dive"
    items: list[dict[str, Any]]  # list of clause_id decisions


class IP3ResumeDecision(TypedDict):
    """Resume payload for IP-3 confirm_submit / save_draft / back_to_review."""
    action: str  # "confirm_submit" | "save_draft" | "back_to_review"


# ──────────────────────────────────────────────
# InterruptSession model dataclass
# ──────────────────────────────────────────────


class InterruptPoint(str, Enum):
    """Three interrupt points defined in the HITL architecture."""
    IP1_HIGH_RISK = "IP-1"
    IP2_MEDIUM_RISK = "IP-2"
    IP3_FINAL_CONFIRM = "IP-3"


class InterruptStatus(str, Enum):
    """InterruptSession lifecycle status."""
    WAITING = "waiting"
    RESOLVED = "resolved"
    TIMEOUT = "timeout"


class RiskLevel(str, Enum):
    """Risk classification levels per business model §4.1."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DecisionType(str, Enum):
    """Human reviewer decision types per data model §3.3."""
    APPROVE = "APPROVE"
    EDIT = "EDIT"
    REJECT = "REJECT"
    MANUAL_ADD = "MANUAL_ADD"
    BATCH_CONFIRM = "BATCH_CONFIRM"
    ESCALATE = "ESCALATE"


class DocumentStatus(str, Enum):
    """9-state document lifecycle."""
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
