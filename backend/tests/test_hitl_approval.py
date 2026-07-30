"""
Human-In-The-Loop Approval Flow Tests.

Covers API Spec §五: all 8 HITL operations with business rule enforcement.
IP-1 (HIGH): approve, edit, reject
IP-2 (MEDIUM): batch-approve, spot-check
Cross-cutting: escalate, manual-add
IP-3 (FINAL): submit, save-draft
"""

from __future__ import annotations

import httpx
import pytest


# ════════════════════════════════════════════════════════════════════
# IP-1: HIGH Risk Individual Operations
# ════════════════════════════════════════════════════════════════════

class TestHighRiskApproval:
    """Approval operations on HIGH risk flags (non-skippable)."""

    async def test_approve_high_risk(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str, risk_flag_ids: dict,
    ):
        """Approve a HIGH risk flag — expect status CONFIRMED."""
        high_ids = risk_flag_ids.get("HIGH", [])
        assert high_ids, "Need at least one HIGH risk flag"
        flag_id = high_ids[0]

        resp = await async_client.post(
            f"/api/v1/risk-flags/{flag_id}/approve",
            json={"comment": "确认该条款确实存在高风险"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Approve failed: {resp.text}"
        data = resp.json()["data"]
        assert data["status"] == "CONFIRMED"
        assert "decision_id" in data
        assert "updated_review_summary" in data

    async def test_edit_risk_flag_downgrade(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str, risk_flag_ids: dict,
    ):
        """Edit a HIGH risk flag to MEDIUM — expect status AMENDED."""
        high_ids = risk_flag_ids.get("HIGH", [])
        assert len(high_ids) >= 2, "Need at least 2 HIGH risk flags"
        flag_id = high_ids[1]

        resp = await async_client.post(
            f"/api/v1/risk-flags/{flag_id}/edit",
            json={
                "comment": "风险等级从HIGH降为MEDIUM，该条款可协商调整",
                "modified_risk_level": "MEDIUM",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Edit failed: {resp.text}"
        data = resp.json()["data"]
        assert data["status"] == "AMENDED"
        assert data["modified_risk_level"] == "MEDIUM"

    async def test_edit_risk_flag_short_comment_fails(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str, risk_flag_ids: dict,
    ):
        """Edit with comment < 10 chars — expect 422 VALIDATION_FAILED."""
        high_ids = risk_flag_ids.get("HIGH", [])
        assert len(high_ids) >= 3, "Need at least 3 HIGH risk flags"
        flag_id = high_ids[2]

        resp = await async_client.post(
            f"/api/v1/risk-flags/{flag_id}/edit",
            json={"comment": "ok", "modified_risk_level": "MEDIUM"},
            headers=auth_headers,
        )
        assert resp.status_code == 422, (
            f"Expected 422 for short comment, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body["code"] == "VALIDATION_FAILED"

    async def test_reject_risk_flag(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str, fake_db, risk_flag_ids: dict,
    ):
        """Reject a HIGH risk flag with valid reason — expect REJECTED."""
        # Get a HIGH flag that hasn't been used yet
        flags = fake_db.risk_flags.get(reviewed_document_id, {})
        high_pending = [
            fid for fid, f in flags.items()
            if f["risk_level"] == "HIGH" and f["status"] == "PENDING_REVIEW"
        ]
        if not high_pending:
            # Create a fresh one
            high_pending = risk_flag_ids.get("HIGH", [])
        assert high_pending, "Need at least one PENDING_REVIEW HIGH flag"
        flag_id = high_pending[0]

        resp = await async_client.post(
            f"/api/v1/risk-flags/{flag_id}/reject",
            json={"reject_reason": "该条款为行业标准表述，不构成实质性风险"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Reject failed: {resp.text}"
        data = resp.json()["data"]
        assert data["status"] == "REJECTED"
        assert data["message"] == "该风险标记已移除"

    async def test_reject_reason_too_short_fails(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        fake_db, risk_flag_ids: dict,
    ):
        """Reject with reason < 10 chars — expect 422 VALIDATION_FAILED."""
        high_ids = risk_flag_ids.get("HIGH", [])
        assert high_ids, "Need at least one HIGH risk flag"
        flag_id = high_ids[0]

        resp = await async_client.post(
            f"/api/v1/risk-flags/{flag_id}/reject",
            json={"reject_reason": "no"},
            headers=auth_headers,
        )
        assert resp.status_code == 422, (
            f"Expected 422 for short reason, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body["code"] == "VALIDATION_FAILED"


# ════════════════════════════════════════════════════════════════════
# IP-2: MEDIUM Risk Batch Operations
# ════════════════════════════════════════════════════════════════════

class TestMediumRiskBatch:
    """Batch-approve and spot-check operations."""

    async def test_batch_approve_medium_risk(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str, risk_flag_ids: dict,
    ):
        """Batch-approve medium risk flags — expect batch_approved_count."""
        medium_ids = risk_flag_ids.get("MEDIUM", [])
        assert medium_ids, "Need at least one MEDIUM risk flag"

        resp = await async_client.post(
            "/api/v1/risk-flags/batch-approve",
            json={
                "document_id": reviewed_document_id,
                "risk_flag_ids": medium_ids,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Batch approve failed: {resp.text}"
        data = resp.json()["data"]
        assert data["batch_approved_count"] == len(medium_ids)

    async def test_spot_check_low_risk(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str,
    ):
        """Spot-check LOW risk flags — expect deterministic sample."""
        resp = await async_client.post(
            "/api/v1/risk-flags/sample",
            json={"document_id": reviewed_document_id, "sample_ratio": 0.11},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Spot check failed: {resp.text}"
        data = resp.json()["data"]
        assert "sampled_risk_flags" in data
        assert "sample_size" in data
        assert "total_low_risk" in data
        assert "seed_info" in data

    async def test_spot_check_deterministic(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str,
    ):
        """Two calls with same params return same sample (deterministic seed)."""
        params = {"document_id": reviewed_document_id, "sample_ratio": 0.11}
        resp1 = await async_client.post(
            "/api/v1/risk-flags/sample", json=params, headers=auth_headers
        )
        resp2 = await async_client.post(
            "/api/v1/risk-flags/sample", json=params, headers=auth_headers
        )
        assert resp1.status_code == 200 and resp2.status_code == 200
        ids1 = [f["risk_flag_id"] for f in resp1.json()["data"]["sampled_risk_flags"]]
        ids2 = [f["risk_flag_id"] for f in resp2.json()["data"]["sampled_risk_flags"]]
        assert ids1 == ids2, f"Spot check should be deterministic: {ids1} vs {ids2}"


# ════════════════════════════════════════════════════════════════════
# Escalate & Manual Add
# ════════════════════════════════════════════════════════════════════

class TestEscalate:
    """Escalate MEDIUM/LOW risk to HIGH (irreversible)."""

    async def test_escalate_to_high(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str, risk_flag_ids: dict,
    ):
        """Escalate a MEDIUM risk flag — expect level HIGH, status ESCALATED_TO_HIGH."""
        medium_ids = risk_flag_ids.get("MEDIUM", [])
        assert medium_ids, "Need at least one MEDIUM risk flag"
        flag_id = medium_ids[0]

        resp = await async_client.post(
            f"/api/v1/risk-flags/{flag_id}/escalate",
            json={"new_level": "HIGH", "reason": "抽样审计发现该条款实际存在较高风险"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Escalate failed: {resp.text}"
        data = resp.json()["data"]
        assert data["new_level"] == "HIGH"
        assert data["status"] == "ESCALATED_TO_HIGH"


class TestManualAdd:
    """Manually add a risk flag (not AI-generated)."""

    async def test_manual_add_risk_flag(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str,
    ):
        """Manually add a risk flag — expect 201 with source MANUALLY_ADDED."""
        resp = await async_client.post(
            "/api/v1/risk-flags/manual",
            json={
                "document_id": reviewed_document_id,
                "clause_location": {
                    "page_number": 5, "paragraph_number": 3,
                    "char_offset_start": 2100, "char_offset_end": 2350,
                    "text_hash": "e5f6g7h8i9",
                },
                "risk_level": "HIGH",
                "risk_category": "财务风险",
                "description": "赔偿上限条款使用了模糊的'合理费用'表述，可能导致争议风险",
                "clause_text": "违约方应赔偿守约方因此产生的合理费用...",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, f"Manual add failed: {resp.text}"
        data = resp.json()["data"]
        assert data["source"] == "MANUALLY_ADDED"
        assert data["risk_level"] == "HIGH"
        assert data["status"] == "PENDING_REVIEW"
        assert "risk_flag_id" in data
        assert "clause_id" in data

    async def test_manual_add_short_description_fails(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str,
    ):
        """Manual add with description < 10 chars — expect 422."""
        resp = await async_client.post(
            "/api/v1/risk-flags/manual",
            json={
                "document_id": reviewed_document_id,
                "clause_location": {"page_number": 1},
                "risk_level": "HIGH",
                "risk_category": "其他",
                "description": "短",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422, (
            f"Expected 422 for short description, got {resp.status_code}: {resp.text}"
        )


# ════════════════════════════════════════════════════════════════════
# IP-3: Final Submit / Save Draft
# ════════════════════════════════════════════════════════════════════

class TestSubmitAndDraft:
    """Submit (IP-3 final confirmation) and save-draft operations."""

    async def test_submit_all_high_resolved_returns_200(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str, risk_flag_ids: dict,
    ):
        """Submit after all HIGH risks are resolved — expect 200 COMPLETED."""
        doc_id = reviewed_document_id
        # Approve all HIGH risk flags first
        high_ids = risk_flag_ids.get("HIGH", [])
        for fid in high_ids:
            await async_client.post(
                f"/api/v1/risk-flags/{fid}/approve",
                json={"comment": "确认高风险合理"},
                headers=auth_headers,
            )

        resp = await async_client.post(
            f"/api/v1/documents/{doc_id}/submit",
            json={"comment": "审阅完成，提交最终报告"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Submit failed: {resp.text}"
        data = resp.json()["data"]
        assert data["status"] == "COMPLETED"
        assert "report_id" in data

    async def test_submit_blocked_by_unresolved_high_returns_409(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        fake_db,
    ):
        """Submit with unresolved HIGH risks — expect 409 CONFLICT."""
        # Create a doc with a HIGH risk that is still PENDING_REVIEW
        doc_id = "d_conflict_test"
        fake_db.documents[doc_id] = {
            "document_id": doc_id, "original_filename": "conflict.pdf",
            "title": "Conflict Test", "document_type": "NDA", "format": "PDF",
            "file_size_bytes": 1000, "page_count": 2,
            "status": "REVIEWED",
            "uploaded_at": "2026-07-30T00:00:00Z",
            "md5_hash": "abc", "ocr_status": "NOT_NEEDED",
            "encryption_status": "NONE",
        }
        fake_db.risk_flags[doc_id] = {
            "rf_block_001": {
                "risk_flag_id": "rf_block_001",
                "clause_id": "cl_001",
                "document_id": doc_id,
                "risk_level": "HIGH",
                "risk_category": "合规风险",
                "ai_confidence": 0.9,
                "status": "PENDING_REVIEW",  # Unresolved!
                "source": "AI_GENERATED",
                "agent_name": "risk_control",
                "rationale_text": "测试未解决高风险",
                "playbook_diff_text": "",
                "regulation_reference": "",
                "suggested_wording": "",
                "clause_location": {},
                "escalated": False,
                "escalated_from": None,
                "sampled": False,
                "created_at": "2026-07-30T00:00:00Z",
                "created_by": "test",
            },
        }

        resp = await async_client.post(
            f"/api/v1/documents/{doc_id}/submit",
            json={"comment": "尝试提交"},
            headers=auth_headers,
        )
        assert resp.status_code == 409, (
            f"Expected 409 CONFLICT, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body["code"] == "CONFLICT"
        assert "高风险" in body["message"]

    async def test_save_draft_any_state(
        self, async_client: httpx.AsyncClient, auth_headers: dict,
        reviewed_document_id: str,
    ):
        """Save draft at any state — expect 200, status unchanged."""
        doc_id = reviewed_document_id
        resp = await async_client.post(
            f"/api/v1/documents/{doc_id}/save-draft",
            json={"comment": "中途保存草稿"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Save draft failed: {resp.text}"
        data = resp.json()["data"]
        assert data["document_id"] == doc_id
        assert "message" in data
