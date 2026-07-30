"""
Report, Export, Sign, Audit, Dashboard, and Playbook Tests.

Covers API Spec §六: report, export PDF, sign, audit-logs,
dashboard stats, and playbook listing.
"""

from __future__ import annotations

import httpx
import pytest


class TestReport:
    """GET /api/v1/documents/{id}/report"""

    async def test_get_report_after_submit(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str, risk_flag_ids: dict,
    ):
        """Submit and get the report — expect 200 with risk_aggregation."""
        doc_id = reviewed_document_id
        # Resolve all HIGH risks first
        for fid in risk_flag_ids.get("HIGH", []):
            await async_client.post(
                f"/api/v1/risk-flags/{fid}/approve",
                json={"comment": "确认该高风险合理"},
                headers=auth_headers,
            )
        # Submit
        submit_resp = await async_client.post(
            f"/api/v1/documents/{doc_id}/submit",
            json={"comment": "审阅完成"},
            headers=auth_headers,
        )
        assert submit_resp.status_code == 200, f"Submit failed: {submit_resp.text}"

        # Get report
        resp = await async_client.get(
            f"/api/v1/documents/{doc_id}/report",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Get report failed: {resp.text}"
        data = resp.json()["data"]
        assert "report_id" in data
        assert data["document_id"] == doc_id
        assert "risk_aggregation" in data
        assert data["sign_status"] == "UNSIGNED"

    async def test_get_report_before_submit_returns_404(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str,
    ):
        """Get report before submitting — expect 404."""
        resp = await async_client.get(
            f"/api/v1/documents/{reviewed_document_id}/report",
            headers=auth_headers,
        )
        assert resp.status_code == 404, (
            f"Expected 404, got {resp.status_code}: {resp.text}"
        )


class TestExportReport:
    """GET /api/v1/documents/{id}/report/export"""

    async def test_export_report_pdf(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str, risk_flag_ids: dict,
    ):
        """Export report as PDF — expect 200 with application/pdf."""
        doc_id = reviewed_document_id
        for fid in risk_flag_ids.get("HIGH", []):
            await async_client.post(
                f"/api/v1/risk-flags/{fid}/approve",
                json={"comment": "确认高风险合理"},
                headers=auth_headers,
            )
        await async_client.post(
            f"/api/v1/documents/{doc_id}/submit",
            json={"comment": "完成"}, headers=auth_headers,
        )

        resp = await async_client.get(
            f"/api/v1/documents/{doc_id}/report/export?format=pdf",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Export failed: {resp.text}"
        content_type = resp.headers.get("content-type", "")
        assert "application/pdf" in content_type, (
            f"Expected PDF content-type, got: {content_type}"
        )
        assert "attachment" in resp.headers.get("content-disposition", "")


class TestSignReport:
    """POST /api/v1/documents/{id}/report/sign"""

    async def test_sign_report(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str, risk_flag_ids: dict,
    ):
        """Sign a report — expect 200 with sign_status=SIGNED."""
        doc_id = reviewed_document_id
        for fid in risk_flag_ids.get("HIGH", []):
            await async_client.post(
                f"/api/v1/risk-flags/{fid}/approve",
                json={"comment": "确认高风险合理"},
                headers=auth_headers,
            )
        await async_client.post(
            f"/api/v1/documents/{doc_id}/submit",
            json={"comment": "完成"}, headers=auth_headers,
        )

        resp = await async_client.post(
            f"/api/v1/documents/{doc_id}/report/sign",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Sign failed: {resp.text}"
        data = resp.json()["data"]
        assert data["sign_status"] == "SIGNED"
        assert "signer_name" in data
        assert "signed_at" in data


class TestAuditLogs:
    """GET /api/v1/documents/{id}/audit-logs"""

    async def test_audit_logs_paginated(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str,
    ):
        """Get audit logs — expect 200 with items list."""
        resp = await async_client.get(
            f"/api/v1/documents/{reviewed_document_id}/audit-logs?page=1&size=50",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Audit logs failed: {resp.text}"
        data = resp.json()["data"]
        assert "page" in data
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)


class TestDashboard:
    """GET /api/v1/dashboard/stats"""

    async def test_dashboard_stats(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
    ):
        """Get dashboard stats — expect 200 with stat fields."""
        resp = await async_client.get(
            "/api/v1/dashboard/stats",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Dashboard failed: {resp.text}"
        data = resp.json()["data"]
        assert "pending_reviews" in data
        assert "completed_this_week" in data
        assert "avg_review_time_minutes" in data
        assert "total_risks_found" in data


class TestPlaybooks:
    """GET /api/v1/playbooks"""

    async def test_get_playbooks(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
    ):
        """List playbooks — expect 200 with array."""
        resp = await async_client.get(
            "/api/v1/playbooks",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Playbooks failed: {resp.text}"
        data = resp.json()["data"]
        assert isinstance(data, list)

    async def test_get_playbooks_filtered_by_type(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
    ):
        """Filter playbooks by doc_type=NDA."""
        resp = await async_client.get(
            "/api/v1/playbooks?doc_type=NDA",
            headers=auth_headers,
        )
        assert resp.status_code == 200
