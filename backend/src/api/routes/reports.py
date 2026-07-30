"""
Report, export, audit, dashboard, and playbook routes.

API Spec: docs/08_api_specification/api_spec-v1.0.md §六
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import CurrentUser, get_current_user
from schemas.common import APIResponse

router = APIRouter(prefix="", tags=["reports"])


# ── Dependencies ────────────────────────────────────────────────────


# TODO: Phase 4+ — replace mock services with real report generation


async def get_report_service():
    """Factory for report service. Overridden in tests."""
    from services.mock_services import MockReportService
    return MockReportService()


# ── Report ──────────────────────────────────────────────────────────


@router.get("/documents/{document_id}/report")
async def get_report(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_report_service),
):
    """Get the review report for a completed document."""
    return await service.get_report(document_id, user)


@router.get("/documents/{document_id}/report/export")
async def export_report_pdf(
    document_id: str,
    format: str = "pdf",
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_report_service),
):
    """Export the review report as PDF."""
    return await service.export_report(document_id, format, user)


@router.post("/documents/{document_id}/report/sign")
async def sign_report(
    document_id: str,
    body: dict[str, Any] = Body(None),
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_report_service),
):
    """Sign the review report."""
    return await service.sign_report(document_id, body, user)


# ── Audit Logs ──────────────────────────────────────────────────────


@router.get("/documents/{document_id}/audit-logs")
async def get_audit_logs(
    document_id: str,
    page: int = 1,
    size: int = 50,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_report_service),
):
    """Get audit trail logs for a document."""
    return await service.get_audit_logs(document_id, page, size, user)


# ── SSE Events ──────────────────────────────────────────────────────


@router.get("/documents/{document_id}/events")
async def get_sse_events(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    service=Depends(get_report_service),
):
    """SSE endpoint for real-time event streaming."""
    return await service.stream_events(document_id, user)


# ── Dashboard & Playbooks ───────────────────────────────────────────


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics.

    API Spec §6.5 — P1 页面 4 张统计卡片.
    """
    from services.dashboard_service import DashboardService

    service = DashboardService(db)
    stats = await service.get_stats(user.user_id)
    return APIResponse(data=stats)


@router.get("/playbooks")
async def get_playbooks(
    doc_type: Optional[str] = Query(default=None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List available playbook rules, optionally filtered by doc_type.

    API Spec §6.6
    """
    from sqlalchemy import select
    from models.playbook import PlaybookRule

    stmt = select(PlaybookRule).where(PlaybookRule.is_active == True)
    if doc_type:
        stmt = stmt.where(PlaybookRule.applicable_doc_type == doc_type)
    stmt = stmt.order_by(PlaybookRule.name)

    result = await db.execute(stmt)
    rules = result.scalars().all()

    items = [
        {
            "playbook_rule_id": r.id,
            "name": r.name,
            "applicable_doc_type": r.applicable_doc_type,
            "risk_level": r.risk_level,
            "risk_category": r.risk_category,
            "version": r.version,
        }
        for r in rules
    ]
    return APIResponse(data=items)
