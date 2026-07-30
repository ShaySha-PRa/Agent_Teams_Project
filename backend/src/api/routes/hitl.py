"""
Human-In-The-Loop approval routes — 8 HITL operations.

API Spec: docs/08_api_specification/api_spec-v1.0.md §五
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from core.security import CurrentUser, get_current_user

router = APIRouter(prefix="", tags=["hitl"])


# ── Dependencies ────────────────────────────────────────────────────


# TODO: Phase 3+ — replace mock services with real LangGraph HITL integration


async def get_hitl_service():
    """Factory for HITL service. Overridden in tests."""
    from services.mock_services import MockHITLService
    return MockHITLService()


# ── IP-1: HIGH risk individual operations ───────────────────────────


@router.post("/risk-flags/{risk_flag_id}/approve")
async def approve_risk_flag(
    risk_flag_id: str,
    body: dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_hitl_service),
):
    """Approve an AI-generated risk flag (confirm the risk exists)."""
    return await service.approve(risk_flag_id, body, user)


@router.post("/risk-flags/{risk_flag_id}/edit")
async def edit_risk_flag(
    risk_flag_id: str,
    body: dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_hitl_service),
):
    """Edit/modify an AI risk flag (change level, category, or suggestion)."""
    return await service.edit(risk_flag_id, body, user)


@router.post("/risk-flags/{risk_flag_id}/reject")
async def reject_risk_flag(
    risk_flag_id: str,
    body: dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_hitl_service),
):
    """Reject an AI risk flag as a false positive."""
    return await service.reject(risk_flag_id, body, user)


# ── IP-2: MEDIUM risk batch operations ──────────────────────────────


@router.post("/risk-flags/batch-approve")
async def batch_approve_risk_flags(
    body: dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_hitl_service),
):
    """Batch-approve medium risk flags (auto-pass)."""
    return await service.batch_approve(body, user)


@router.post("/risk-flags/sample")
async def spot_check_sample(
    body: dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_hitl_service),
):
    """Get a deterministic sample of LOW risk flags for spot-check audit."""
    return await service.spot_check(body, user)


# ── Escalate ────────────────────────────────────────────────────────


@router.post("/risk-flags/{risk_flag_id}/escalate")
async def escalate_risk_flag(
    risk_flag_id: str,
    body: dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_hitl_service),
):
    """Escalate a MEDIUM/LOW risk flag to HIGH (irreversible)."""
    return await service.escalate(risk_flag_id, body, user)


# ── Manual Add ──────────────────────────────────────────────────────


@router.post("/risk-flags/manual", status_code=status.HTTP_201_CREATED)
async def manual_add_risk_flag(
    body: dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_hitl_service),
):
    """Manually add a new risk flag (not AI-generated)."""
    return await service.manual_add(body, user)


# ── IP-3: Final Submit / Save Draft ─────────────────────────────────


@router.post("/documents/{document_id}/submit")
async def submit_document(
    document_id: str,
    body: dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_hitl_service),
):
    """Submit the review — all HIGH risk flags must be resolved."""
    return await service.submit(document_id, body, user)


@router.post("/documents/{document_id}/save-draft")
async def save_draft(
    document_id: str,
    body: dict[str, Any] | None = Body(default=None),
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_hitl_service),
):
    """Save current approval state as a draft (any state)."""
    return await service.save_draft(document_id, body or {}, user)
