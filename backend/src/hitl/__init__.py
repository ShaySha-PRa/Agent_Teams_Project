"""
HITL (Human-In-The-Loop) Package.

Provides the full HITL workflow implementation for the Agent 智能文档审核系统:

- 3 InterruptPoint implementations (IP-1 HIGH, IP-2 MEDIUM, IP-3 FINAL)
- ``HumanInTheLoopMiddleware`` with per-risk-level ``InterruptOnConfig``
- 8 ``Command(resume)`` handlers mapped from frontend HTTP operations
- ``InterruptSession`` model and lifecycle manager
- Risk classification (HIGH / MEDIUM / LOW scoring)
- 4-layer constraint validators (Graph / API / StateMachine / Audit)

Usage::

    from hitl import (
        # Interrupt points
        ip1_high_risk,
        ip2_medium_risk,
        ip3_final_confirm,
        # Middleware
        create_hitl_middleware,
        create_deepseek_model,
        # Command handlers
        handle_approve,
        handle_edit,
        handle_reject,
        handle_batch_approve,
        handle_spot_check,
        handle_escalate,
        handle_manual_add,
        handle_final_submit,
        # Session management
        InterruptSession,
        InterruptSessionManager,
        # Risk classification
        classify_risk,
        RiskClassification,
        # Constraints
        ImmutableAuditLog,
        log_immutable_decision,
        validate_status_transition,
        enforce_ip1_non_skippable,
        enforce_high_risk_completion,
        # Types
        DocumentReviewState,
        RiskLevel,
        InterruptPoint,
    )
"""

from .command_handler import (
    handle_approve,
    handle_batch_approve,
    handle_edit,
    handle_escalate,
    handle_final_submit,
    handle_manual_add,
    handle_reject,
    handle_spot_check,
)
from .constraints import (
    ConstraintViolationError,
    ImmutableAuditLog,
    enforce_high_risk_completion,
    enforce_ip1_non_skippable,
    log_immutable_decision,
    validate_status_transition,
)
from .interrupt_points import (
    ip1_high_risk,
    ip2_medium_risk,
    ip3_final_confirm,
)
from .interrupt_session import (
    InterruptSession,
    InterruptSessionManager,
)
from .middleware import (
    create_deepseek_model,
    create_hitl_middleware,
)
from .risk_classifier import (
    RiskClassification,
    classify_batch,
    classify_risk,
)
from .types import (
    DecisionType,
    DocumentReviewState,
    DocumentStatus,
    IP1Payload,
    IP2BatchItem,
    IP2Payload,
    IP3Payload,
    InterruptPoint,
    InterruptStatus,
    RiskLevel,
)

__all__ = [
    # Interrupt points
    "ip1_high_risk",
    "ip2_medium_risk",
    "ip3_final_confirm",
    # Middleware
    "create_hitl_middleware",
    "create_deepseek_model",
    # Command handlers
    "handle_approve",
    "handle_edit",
    "handle_reject",
    "handle_batch_approve",
    "handle_spot_check",
    "handle_escalate",
    "handle_manual_add",
    "handle_final_submit",
    # Session
    "InterruptSession",
    "InterruptSessionManager",
    # Risk classifier
    "classify_risk",
    "classify_batch",
    "RiskClassification",
    # Constraints
    "ConstraintViolationError",
    "ImmutableAuditLog",
    "log_immutable_decision",
    "enforce_ip1_non_skippable",
    "enforce_high_risk_completion",
    "validate_status_transition",
    # Types
    "DocumentReviewState",
    "DocumentStatus",
    "InterruptPoint",
    "InterruptStatus",
    "RiskLevel",
    "DecisionType",
    "IP1Payload",
    "IP2Payload",
    "IP2BatchItem",
    "IP3Payload",
]
