"""
AI Review routes — start, control, and query review tasks.

API Spec: docs/08_api_specification/api_spec-v1.0.md §四
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.security import CurrentUser, get_current_user

router = APIRouter(prefix="", tags=["review"])


# ── Dependencies ────────────────────────────────────────────────────


# TODO: Phase 2+ — replace mock services with real LangGraph WorkflowRunner integration


async def get_review_service():
    """Factory for review service. Overridden in tests."""
    from services.mock_services import MockReviewService
    return MockReviewService()


async def get_clause_service():
    """Factory for clause query service. Overridden in tests."""
    from services.mock_services import MockClauseService
    return MockClauseService()


async def get_risk_flag_service():
    """Factory for risk flag service. Overridden in tests."""
    from services.mock_services import MockRiskFlagService
    return MockRiskFlagService()


# ── Review Task Control ─────────────────────────────────────────────


@router.post("/documents/{document_id}/review", status_code=status.HTTP_202_ACCEPTED)
async def start_review(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_review_service),
):
    """Start AI review on a PARSED document."""
    return await service.start_review(document_id, user)


@router.post("/documents/{document_id}/review/pause")
async def pause_review(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_review_service),
):
    """Pause an active review at the next safe-point."""
    return await service.pause_review(document_id, user)


@router.post("/documents/{document_id}/review/resume")
async def resume_review(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_review_service),
):
    """Resume a paused review from the last checkpoint."""
    return await service.resume_review(document_id, user)


@router.post("/documents/{document_id}/review/cancel")
async def cancel_review(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_review_service),
):
    """Cancel an active review and mark as CANCELLED."""
    return await service.cancel_review(document_id, user)


@router.post("/documents/{document_id}/review/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_review(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_review_service),
):
    """Retry a failed review from the last checkpoint."""
    return await service.retry_review(document_id, user)


# ── Query Endpoints ─────────────────────────────────────────────────


@router.get("/documents/{document_id}/clauses")
async def get_clauses(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_clause_service),
):
    """Get extracted clauses for a document."""
    return await service.get_clauses(document_id, user)


@router.get("/documents/{document_id}/risk-flags")
async def get_risk_flags(
    document_id: str,
    level: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    category: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_risk_flag_service),
):
    """Get risk flags for a document with optional filters."""
    return await service.get_risk_flags(
        document_id, level, status_filter, category, source, user
    )


@router.get("/risk-flags/{risk_flag_id}/playbook-diff")
async def get_playbook_diff(
    risk_flag_id: str,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_risk_flag_service),
):
    """Get playbook comparison diff for a risk flag."""
    return await service.get_playbook_diff(risk_flag_id, user)


@router.get("/risk-flags/{risk_flag_id}/decisions")
async def get_risk_flag_decisions(
    risk_flag_id: str,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_risk_flag_service),
):
    """Get decision history for a risk flag."""
    return await service.get_decisions(risk_flag_id, user)


@router.get("/documents/{document_id}/review-summary")
async def get_review_summary(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_review_service),
):
    """Get approval progress summary for a document."""
    return await service.get_review_summary(document_id, user)
