"""
Risk Classification Logic.

Aligned with:
- business_model.md §4.1 (graded alerting: HIGH / MEDIUM / LOW)
- langchain_hitl_arch-v1.0.md §5 (3 interrupt points by risk level)

Determines:
  1. Risk level (HIGH / MEDIUM / LOW) from AI confidence + playbook match + category.
  2. Whether a given risk requires an interrupt (IP-1 / IP-2 / auto-passed).
  3. Auto-pass conditions for LOW-risk items.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import RiskLevel


# ──────────────────────────────────────────────
# Risk category weights (business model §4.1)
# ──────────────────────────────────────────────

# Higher weight = more severe. Used as a multiplier when computing
# the final risk score from AI confidence + playbook match similarity.
_RISK_CATEGORY_WEIGHTS: dict[str, float] = {
    "合规风险": 1.0,  # highest severity
    "责任风险": 0.95,
    "财务风险": 0.9,
    "违约救济": 0.85,
    "知识产权风险": 0.85,
    "保密义务": 0.8,
    "保密期限": 0.75,
    "存续条款": 0.7,
    "争议解决": 0.65,
    "管辖法律": 0.6,
    "例外情形": 0.55,
    "通知条款": 0.5,
    "可转让性": 0.45,
    "完整协议": 0.4,
    "一般条款": 0.35,  # lowest severity
}


# ──────────────────────────────────────────────
# Match type penalty factors
# ──────────────────────────────────────────────

_MATCH_TYPE_FACTOR: dict[str, float] = {
    "MISMATCHED": 1.0,  # full penalty — stark difference
    "PARTIAL": 0.6,  # partial penalty — some alignment
    "SEMANTIC": 0.3,  # minor penalty — semantically close
    "EXACT": 0.0,  # no penalty — matches standard
}


# ──────────────────────────────────────────────
# Thresholds
# ──────────────────────────────────────────────

HIGH_THRESHOLD = 0.70  # risk_score >= 0.70 → HIGH
MEDIUM_THRESHOLD = 0.40  # risk_score >= 0.40 → MEDIUM
# risk_score < 0.40 → LOW

LOW_AUTO_PASS_CONFIDENCE = 0.50  # LOW risk with AI confidence < 0.50 → auto-pass


# ──────────────────────────────────────────────
# Result dataclass
# ──────────────────────────────────────────────


@dataclass
class RiskClassification:
    """Result of risk classification for a single clause."""

    risk_level: RiskLevel
    risk_score: float  # 0.0–1.0 composite score
    ai_confidence: float  # raw AI confidence
    category_weight: float  # weight applied from category
    match_factor: float  # factor applied from playbook match type
    requires_interrupt: bool = True
    interrupt_point: str = ""  # "IP-1" or "IP-2"
    reasoning: str = ""  # human-readable rationale


# ──────────────────────────────────────────────
# Main classifier
# ──────────────────────────────────────────────


def classify_risk(
    *,
    ai_confidence: float,
    risk_category: str,
    match_type: str,  # "EXACT" | "SEMANTIC" | "PARTIAL" | "MISMATCHED"
    clause_text: str = "",
    clause_type: str = "",
) -> RiskClassification:
    """Classify a clause's risk level from AI confidence, category, and match.

    Composite formula::

        category_w = _RISK_CATEGORY_WEIGHTS.get(category, 0.5)
        match_f    = _MATCH_TYPE_FACTOR.get(match_type, 0.5)
        risk_score = 0.6 * ai_confidence + 0.25 * category_w + 0.15 * match_f

    Thresholds:
        - risk_score >= 0.70 → HIGH   → IP-1 (mandatory)
        - risk_score >= 0.40 → MEDIUM → IP-2 (batch-optional)
        - risk_score <  0.40 → LOW    → auto-passed (no interrupt)

    Args:
        ai_confidence: AI agent confidence (0.0–1.0).
        risk_category: One of the 15 risk categories.
        match_type: Playbook match classification.
        clause_text: Original clause text (used in reasoning).
        clause_type: Clause type enum (used in reasoning).

    Returns:
        ``RiskClassification`` with level, score, and interrupt routing.
    """
    # Clamp inputs
    ai_confidence = max(0.0, min(1.0, ai_confidence))
    category_weight = _RISK_CATEGORY_WEIGHTS.get(risk_category, 0.5)
    match_factor = _MATCH_TYPE_FACTOR.get(match_type, 0.5)

    # Composite score: weighted blend
    risk_score = (
        0.60 * ai_confidence
        + 0.25 * category_weight
        + 0.15 * match_factor
    )

    # Route to interrupt point
    if risk_score >= HIGH_THRESHOLD:
        level = RiskLevel.HIGH
        requires_interrupt = True
        interrupt_point = "IP-1"
        reasoning = _build_reasoning(
            level, risk_score, ai_confidence, category_weight,
            match_factor, risk_category, match_type
        )
    elif risk_score >= MEDIUM_THRESHOLD:
        level = RiskLevel.MEDIUM
        requires_interrupt = True  # interrupt exists but batch-skippable
        interrupt_point = "IP-2"
        reasoning = _build_reasoning(
            level, risk_score, ai_confidence, category_weight,
            match_factor, risk_category, match_type
        )
    else:
        level = RiskLevel.LOW
        requires_interrupt = False  # auto-passed
        interrupt_point = ""
        reasoning = _build_reasoning(
            level, risk_score, ai_confidence, category_weight,
            match_factor, risk_category, match_type
        )

    return RiskClassification(
        risk_level=level,
        risk_score=round(risk_score, 4),
        ai_confidence=ai_confidence,
        category_weight=category_weight,
        match_factor=match_factor,
        requires_interrupt=requires_interrupt,
        interrupt_point=interrupt_point,
        reasoning=reasoning,
    )


# ──────────────────────────────────────────────
# Auto-pass condition
# ──────────────────────────────────────────────


def auto_pass_condition(
    *,
    risk_level: str,
    ai_confidence: float,
    is_manually_added: bool = False,
) -> bool:
    """Determine whether a risk flag can be auto-passed (no human review).

    Auto-pass rules:
        1. ``risk_level == "LOW"`` **and** ``ai_confidence < 0.50`` → auto-pass.
        2. Manually-added flags are **never** auto-passed (human intent).
        3. HIGH / MEDIUM flags are **never** auto-passed.

    Args:
        risk_level: ``"HIGH"``, ``"MEDIUM"``, or ``"LOW"``.
        ai_confidence: AI confidence score.
        is_manually_added: ``True`` if the flag was manually created.

    Returns:
        ``True`` if the flag can be auto-passed without human review.
    """
    if is_manually_added:
        return False
    if risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM):
        return False
    # LOW risk
    return ai_confidence < LOW_AUTO_PASS_CONFIDENCE


# ──────────────────────────────────────────────
# Batch classification helper
# ──────────────────────────────────────────────


def classify_batch(
    flags: list[dict[str, Any]],
) -> list[RiskClassification]:
    """Classify a batch of risk flags in one pass.

    Args:
        flags: List of dicts with keys: ``ai_confidence``, ``risk_category``,
            ``match_type``, ``clause_text``, ``clause_type``.

    Returns:
        List of ``RiskClassification`` results, one per input flag.
    """
    results: list[RiskClassification] = []
    for f in flags:
        result = classify_risk(
            ai_confidence=f.get("ai_confidence", 0.0),
            risk_category=f.get("risk_category", "一般条款"),
            match_type=f.get("match_type", "PARTIAL"),
            clause_text=f.get("clause_text", ""),
            clause_type=f.get("clause_type", ""),
        )
        results.append(result)
    return results


# ──────────────────────────────────────────────
# Reasoning builder
# ──────────────────────────────────────────────


def _build_reasoning(
    level: RiskLevel,
    score: float,
    confidence: float,
    cat_w: float,
    match_f: float,
    category: str,
    match_type: str,
) -> str:
    """Build a human-readable classification rationale."""
    parts = [
        f"风险等级={level.value}",
        f"综合评分={score:.3f}",
        f"AI置信度={confidence:.2f}",
        f"类别权重({category})={cat_w:.2f}",
        f"匹配度({match_type})={match_f:.2f}",
    ]
    return "; ".join(parts)
