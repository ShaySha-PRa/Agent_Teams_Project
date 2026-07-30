"""
HumanInTheLoopMiddleware Configuration.

Aligned with langchain_hitl_arch-v1.0.md §2.2 (MCP-verified API signatures)
and §5 (3 interrupt points with risk-level-gated tool control).

Uses:
- ``langchain.agents.middleware.HumanInTheLoopMiddleware``
- ``langchain.agents.middleware.InterruptOnConfig``
- ``langgraph.types.Command``  (for resume)

DeepSeek model:
  ChatOpenAI(model="deepseek-chat",
             base_url="https://api.deepseek.com/v1",
             api_key=os.getenv("DEEPSEEK_API_KEY", ""))
"""

from __future__ import annotations

import os

from langchain.agents.middleware.human_in_the_loop import (
    HumanInTheLoopMiddleware,
    InterruptOnConfig,
)
from langchain_openai import ChatOpenAI


# ──────────────────────────────────────────────
# DeepSeek model factory (single source of truth)
# ──────────────────────────────────────────────

def create_deepseek_model(
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> ChatOpenAI:
    """Create a ChatOpenAI instance pointed at DeepSeek.

    Args:
        temperature: Sampling temperature (0.0–2.0). Default 0.1 for
            deterministic classification tasks.
        max_tokens: Max tokens per completion.

    Returns:
        Configured ``ChatOpenAI`` instance.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    return ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# ──────────────────────────────────────────────
# Tool-names mapped by risk level  (spec §5)
# ──────────────────────────────────────────────

# These tool names are the "actions" the Agent can request; the middleware
# intercepts calls to them and pauses for human approval.

_TOOL_NAMES = {
    "high_risk_review": "high_risk_review",  # IP-1: approve / edit / reject
    "medium_risk_review": "medium_risk_review",  # IP-2: batch_confirm / deep_dive
    "final_confirm": "final_confirm",  # IP-3: confirm_submit / save_draft
    "manual_add_risk_flag": "manual_add_risk_flag",  # No interrupt (direct write)
}


# ──────────────────────────────────────────────
# InterruptOnConfig per risk level
# ──────────────────────────────────────────────

HIGH_RISK_INTERRUPT_CONFIG = InterruptOnConfig(
    allowed_decisions=[
        {
            "decision": "approve",
            "name": "Approval",
            "description": "Confirm the AI risk assessment is correct.",
        },
        {
            "decision": "edit",
            "name": "Amendment",
            "description": "Modify the risk level, category, or suggested wording.",
        },
        {
            "decision": "reject",
            "name": "Rejection",
            "description": "Dismiss the AI risk assessment as a false positive.",
        },
    ],
    description=(
        "HIGH-risk clause detected. This item requires mandatory human review "
        "before the workflow can continue."
    ),
)

MEDIUM_RISK_INTERRUPT_CONFIG = InterruptOnConfig(
    allowed_decisions=[
        {
            "decision": "batch_confirm",
            "name": "Batch Confirm All",
            "description": "Auto-pass all medium-risk items without individual review.",
        },
        {
            "decision": "deep_dive",
            "name": "Spot Check Sample",
            "description": "Review a deterministic sample before passing the rest.",
        },
    ],
    description=(
        "MEDIUM-risk items detected. You may batch-confirm to skip, or "
        "spot-check a deterministic sample."
    ),
)

FINAL_CONFIRM_CONFIG = InterruptOnConfig(
    allowed_decisions=[
        {
            "decision": "confirm_submit",
            "name": "Submit Review",
            "description": "Finalize the review, generate the report, and complete the workflow.",
        },
        {
            "decision": "save_draft",
            "name": "Save Draft",
            "description": "Save all current decisions without finalizing.",
        },
        {
            "decision": "back_to_review",
            "name": "Return to Review",
            "description": "Go back to the manual review workspace.",
        },
    ],
    description=(
        "All risk items have been reviewed. Confirm submission to generate "
        "the final audit report."
    ),
)

# manual_add uses NO interrupt (direct state write per spec §5.7)
_MANUAL_ADD_NO_INTERRUPT = False  # False = auto-approved


# ──────────────────────────────────────────────
# Middleware factory
# ──────────────────────────────────────────────

def create_hitl_middleware() -> HumanInTheLoopMiddleware:
    """Create the HITL middleware with per-risk-level interrupt configs.

    The returned middleware is ready to be passed to ``create_agent()``:

    .. code-block:: python

        from langchain.agents import create_agent

        agent = create_agent(
            model=create_deepseek_model(),
            tools=[high_risk_review, medium_risk_review, final_confirm],
            middleware=[create_hitl_middleware()],
            checkpointer=checkpointer,
        )

    Returns:
        Configured ``HumanInTheLoopMiddleware`` instance.
    """
    interrupt_on: dict[str, bool | InterruptOnConfig] = {
        _TOOL_NAMES["high_risk_review"]: HIGH_RISK_INTERRUPT_CONFIG,
        _TOOL_NAMES["medium_risk_review"]: MEDIUM_RISK_INTERRUPT_CONFIG,
        _TOOL_NAMES["final_confirm"]: FINAL_CONFIRM_CONFIG,
        _TOOL_NAMES["manual_add_risk_flag"]: _MANUAL_ADD_NO_INTERRUPT,
    }

    return HumanInTheLoopMiddleware(
        interrupt_on=interrupt_on,
        description_prefix="[HITL] Document Review — human approval required",
    )
