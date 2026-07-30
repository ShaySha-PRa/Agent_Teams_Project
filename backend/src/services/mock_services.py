"""Mock services for Phase 2-4 backend integration with frontend.

These provide correct API contract responses until real LangGraph
workflow integration is complete.  Extracted from tests/conftest.py
where the same mocks drive the 55-test suite.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import io, json

# ─────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class InMemoryDB:
    """In-memory state shared across all mock services within one process."""
    risk_flags: dict[str, dict] = field(default_factory=dict)        # doc_id -> {flag_id: flag}
    decisions: dict[str, list[dict]] = field(default_factory=dict)   # flag_id -> [decisions]
    reports: dict[str, dict] = field(default_factory=dict)           # doc_id -> report
    audit_logs: list[dict] = field(default_factory=list)
    doc_states: dict[str, str] = field(default_factory=dict)         # doc_id -> status

# Module-level singleton shared by all mock services
_db = InMemoryDB()

async def get_mock_db() -> InMemoryDB:
    return _db

def _ok(d):
    return {"code": 0, "message": "success", "data": d, "request_id": f"req_{uuid.uuid4().hex[:8]}"}


def make_mock_clauses(doc_id: str) -> list[dict]:
    """Return clauses with nested `location` matching frontend Clause type."""
    types_ = [
        "保密义务", "保密期限", "例外情形", "违约救济",
        "存续条款", "管辖法律", "争议解决", "通知条款",
        "可转让性", "完整协议", "保密义务补充", "保密期限补充",
    ]
    return [{
        "clause_id": f"cl_{doc_id}_{i+1:03d}",
        "clause_type": ct,
        "clause_text": f"【{ct}】第{i+1}条测试条款原文。接收方同意对披露方的保密信息予以严格保密，未经披露方书面同意不得向任何第三方披露。",
        "extraction_confidence": round(0.85 + i * 0.01, 2),
        "location": {
            "page_number": 1 + i // 3,
            "paragraph_number": i + 1,
            "char_offset_start": 1000 + i * 500,
            "char_offset_end": 1200 + i * 500,
            "text_hash": hashlib.sha256(f"clause_{i}".encode()).hexdigest()[:16],
        },
        "source": "AI",
    } for i, ct in enumerate(types_)]


def make_mock_risk_flags(doc_id: str) -> dict[str, dict]:
    """Return risk flags matching frontend RiskFlag type with clause_text included."""
    clauses = make_mock_clauses(doc_id)
    risk_data = [
        (0, "HIGH", "合规风险"), (1, "HIGH", "保密期限"), (3, "HIGH", "财务风险"),
        (2, "MEDIUM", "例外情形"), (4, "MEDIUM", "存续条款"),
        (5, "MEDIUM", "管辖法律"), (6, "MEDIUM", "争议解决"),
        (7, "MEDIUM", "通知条款"),
        (8, "LOW", "可转让性"), (9, "LOW", "完整协议"), (10, "LOW", "运营风险"), (11, "LOW", "法律风险"),
    ]
    flags = {}
    for idx, (ci, level, cat) in enumerate(risk_data):
        fid = f"rf_{doc_id}_{idx+1:03d}"
        c = clauses[ci] if ci < len(clauses) else clauses[0]
        flags[fid] = {
            "risk_flag_id": fid, "clause_id": c["clause_id"], "document_id": doc_id,
            "risk_level": level, "risk_category": cat,
            "ai_confidence": round(0.75 + idx * 0.02, 2),
            "status": "PENDING_REVIEW" if level == "HIGH" else ("UNREVIEWED_AUTO_PASSED" if level == "MEDIUM" else "UNREVIEWED_AUTO_PASSED"),
            "source": "AI_GENERATED",
            "rationale_text": f"AI: {c['clause_type']}存在{level}风险",
            "playbook_diff_text": f"标准条款: 行业标准\n实际条款: {c['clause_text'][:50]}...",
            "regulation_reference": "相关法规",
            "suggested_wording": "建议修改为行业标准表述",
            "clause_location": c["location"],
            "clause_text": c["clause_text"],
            "escalated": False,
            "escalated_from": None,
            "sampled": level == "LOW",
            "created_at": _utcnow(),
        }
    return flags


# ─────────────────────────────────────────────────────────────────
# Mock Review Service (10 endpoints: review/control/clauses/risk-flags/playbook-diff/decisions/summary)
# ─────────────────────────────────────────────────────────────────

class MockReviewService:
    async def start_review(self, doc_id, user):
        if doc_id not in _db.risk_flags:
            _db.risk_flags.setdefault(doc_id, make_mock_risk_flags(doc_id))
        _db.doc_states[doc_id] = "REVIEWING"
        return _ok({"document_id": doc_id, "review_task_id": f"rt_{doc_id}",
                     "status": "REVIEWING", "thread_id": f"thread_{uuid.uuid4().hex[:8]}",
                     "message": "AI审核已启动"})

    async def pause_review(self, doc_id, user):
        return _ok({"document_id": doc_id, "paused": True})

    async def resume_review(self, doc_id, user):
        return _ok({"document_id": doc_id, "paused": False})

    async def cancel_review(self, doc_id, user):
        _db.doc_states[doc_id] = "CANCELLED"
        return _ok({"document_id": doc_id, "status": "CANCELLED"})

    async def retry_review(self, doc_id, user):
        return _ok({"document_id": doc_id, "review_task_id": f"rt_{doc_id}_retry",
                     "status": "REVIEWING", "message": "审核重试已启动"})

    async def get_review_summary(self, doc_id, user):
        flags = _db.risk_flags.get(doc_id, {})
        high = [f for f in flags.values() if f["risk_level"] == "HIGH"]
        appr = len([f for f in high if f["status"] not in ("PENDING_REVIEW",)])
        return _ok({
            "document_id": doc_id,
            "total_high_risk": len(high), "approved_high_risk": appr,
            "total_medium_risk": len([f for f in flags.values() if f["risk_level"] == "MEDIUM"]),
            "reviewed_medium_risk": len([f for f in flags.values() if f["risk_level"] == "MEDIUM" and f["status"] not in ("UNREVIEWED_AUTO_PASSED",)]),
            "low_risk_auto_passed": len([f for f in flags.values() if f["risk_level"] == "LOW"]),
            "manual_added": len([f for f in flags.values() if f["source"] == "MANUALLY_ADDED"]),
            "completion_rate_pct": round(appr / len(high) * 100 if high else 100, 1),
            "all_high_risk_resolved": appr >= len(high),
        })


class MockClauseService:
    async def get_clauses(self, doc_id, user):
        return _ok({"clauses": make_mock_clauses(doc_id)})


class MockRiskFlagService:
    async def get_risk_flags(self, doc_id, level, status_f, category, source, user):
        # Ensure flags exist for this doc
        if doc_id not in _db.risk_flags:
            _db.risk_flags.setdefault(doc_id, make_mock_risk_flags(doc_id))
        flags = list(_db.risk_flags.get(doc_id, {}).values())
        if level: flags = [f for f in flags if f["risk_level"] == level.upper()]
        if status_f: flags = [f for f in flags if f["status"] == status_f]
        if category: flags = [f for f in flags if f["risk_category"] == category]
        if source: flags = [f for f in flags if f["source"] == source]
        return _ok({"risk_flags": flags})

    async def get_playbook_diff(self, risk_flag_id, user):
        f = self._find_flag(risk_flag_id)
        return _ok({
            "risk_flag_id": risk_flag_id,
            "playbook_rule": {"playbook_rule_id": "pr_001", "name": "NDA-Rule-" + f["risk_category"],
                              "standard_clause_text": "标准行业条款", "risk_level": f["risk_level"],
                              "risk_category": f["risk_category"]},
            "match": {"match_type": "PARTIAL", "similarity_score": 0.42,
                      "diff_items": [{"field": f["risk_category"], "standard_value": "3年", "actual_value": "永久",
                                      "deviation_type": "MISMATCHED"}]}})

    async def get_decisions(self, risk_flag_id, user):
        return _ok({"risk_flag_id": risk_flag_id,
                "decisions": _db.decisions.get(risk_flag_id, [])})

    def _find_flag(self, rid):
        for fl in _db.risk_flags.values():
            if rid in fl: return fl[rid]
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": f"Risk flag {rid} not found",
            "data": None, "request_id": "req_test"})


# ─────────────────────────────────────────────────────────────────
# Mock HITL Service (8 operations)
# ─────────────────────────────────────────────────────────────────

class MockHITLService:
    async def approve(self, rid, body, user):
        f = self._f(rid); f["status"] = "CONFIRMED"
        self._log(rid, "APPROVE", user, body.get("comment", ""))
        return self._resp(rid, "CONFIRMED", self._sum(f["document_id"]))

    async def edit(self, rid, body, user):
        f = self._f(rid); c = body.get("comment", "")
        if len(c) < 10:
            raise HTTPException(status_code=422, detail={
                "code": "VALIDATION_FAILED", "message": "comment must be >= 10 chars",
                "data": None, "request_id": "req_test"})
        nl = body.get("modified_risk_level")
        if nl and nl not in ("HIGH", "MEDIUM", "LOW"):
            raise HTTPException(status_code=422, detail={
                "code": "VALIDATION_FAILED", "message": f"Invalid level: {nl}",
                "data": None, "request_id": "req_test"})
        if nl: f["risk_level"] = nl
        f["status"] = "AMENDED"
        self._log(rid, "EDIT", user, c, modified_risk_level=nl)
        return self._resp(rid, "AMENDED", self._sum(f["document_id"]),
                          modified_risk_level=nl)

    async def reject(self, rid, body, user):
        f = self._f(rid); r = body.get("reject_reason", "")
        if len(r) < 10:
            raise HTTPException(status_code=422, detail={
                "code": "VALIDATION_FAILED", "message": "reject_reason must be >= 10 chars",
                "data": None, "request_id": "req_test"})
        f["status"] = "REJECTED"
        self._log(rid, "REJECT", user, r)
        return {"code": 0, "data": {"risk_flag_id": rid, "status": "REJECTED",
                "decision_id": f"d_{uuid.uuid4().hex[:12]}", "message": "该风险标记已移除"},
                "message": "success", "request_id": "req_test"}

    async def batch_approve(self, body, user):
        did = body.get("document_id", ""); fids = body.get("risk_flag_ids", [])
        fl = _db.risk_flags.get(did, {}); cnt = 0
        for fi in fids:
            if fi in fl:
                fl[fi]["status"] = "REVIEWED_CONFIRMED"; cnt += 1
        self._log_batch(did, fids, "BATCH_CONFIRM", user)
        return _ok({"batch_approved_count": cnt,
                "updated_review_summary": {"reviewed_medium_risk": cnt}})

    async def spot_check(self, body, user):
        did = body.get("document_id", ""); r = body.get("sample_ratio", 0.11)
        fl = _db.risk_flags.get(did, {})
        lo = [f for f in fl.values() if f["risk_level"] == "LOW"]
        n = max(1, int(len(lo) * r)); s = lo[:n]
        # Mark sampled flags
        for f in s:
            f["sampled"] = True
        return _ok({"sampled_risk_flags": s, "sample_size": n,
                "total_low_risk": len(lo), "seed_info": f"sha256({did})[:8]"})

    async def escalate(self, rid, body, user):
        f = self._f(rid); nl = body.get("new_level", "HIGH")
        old_level = f["risk_level"]
        f["risk_level"] = nl; f["status"] = "ESCALATED_TO_HIGH"
        f["escalated"] = True; f["escalated_from"] = old_level
        self._log(rid, "ESCALATE", user, body.get("reason", ""), new_level=nl)
        return _ok({"risk_flag_id": rid, "new_level": nl,
                "status": "ESCALATED_TO_HIGH", "message": "已升级为高风险"})

    async def manual_add(self, body, user):
        d = body.get("description", "")
        if len(d) < 10:
            raise HTTPException(status_code=422, detail={
                "code": "VALIDATION_FAILED", "message": "description must be >= 10 chars",
                "data": None, "request_id": "req_test"})
        did = body.get("document_id", "")
        clause_loc = body.get("clause_location", {})
        fid = f"rf_manual_{uuid.uuid4().hex[:12]}"
        cid = f"cl_manual_{uuid.uuid4().hex[:8]}"
        nf = {"risk_flag_id": fid, "clause_id": cid,
              "document_id": did, "risk_level": body.get("risk_level", "HIGH"),
              "risk_category": body.get("risk_category", "合规风险"), "ai_confidence": 0.0,
              "status": "PENDING_REVIEW", "source": "MANUALLY_ADDED",
              "rationale_text": d, "playbook_diff_text": "手动标记，无 Playbook 对比",
              "regulation_reference": "", "suggested_wording": "",
              "clause_location": clause_loc,
              "clause_text": body.get("clause_text", ""),
              "escalated": False, "escalated_from": None, "sampled": False,
              "created_at": _utcnow()}
        _db.risk_flags.setdefault(did, {})[fid] = nf
        self._log(fid, "MANUAL_ADD", user, d)
        return _ok({"risk_flag_id": fid, "clause_id": cid,
                "risk_level": nf["risk_level"], "status": "PENDING_REVIEW",
                "source": "MANUALLY_ADDED"})

    async def submit(self, did, body, user):
        flags = _db.risk_flags.get(did, {})
        unr = [f for f in flags.values()
               if f["risk_level"] == "HIGH" and f["status"] == "PENDING_REVIEW"]
        if unr:
            raise HTTPException(status_code=409, detail={
                "code": "CONFLICT", "message": f"仍有 {len(unr)} 项高风险条款待审批",
                "data": None, "request_id": "req_test"})
        rid = f"rpt_{did}"
        _db.reports[did] = {"report_id": rid, "document_id": did,
            "generated_at": _utcnow(), "sign_status": "UNSIGNED",
            "risk_aggregation": {"high_confirmed": 2, "high_amended": 1, "high_rejected": 0,
                                 "medium_auto_passed": 4, "medium_reviewed": 1,
                                 "low_auto_passed": 3, "low_spot_checked": 1, "manual_added": 1},
            "high_risk_details": self._high_risk_details(flags),
            "audit_timeline": _db.audit_logs[-20:]}
        _db.doc_states[did] = "COMPLETED"
        _db.audit_logs.append({
            "log_id": f"log_{uuid.uuid4().hex[:12]}", "operation_type": "FINAL_SUBMIT",
            "timestamp": _utcnow(), "operator_id": user.user_id,
            "details": {"document_id": did}})
        return _ok({"document_id": did, "status": "COMPLETED",
                "report_id": rid, "message": "审阅已提交，报告生成中"})

    async def save_draft(self, did, body, user):
        _db.doc_states[did] = "DRAFT"
        _db.audit_logs.append({
            "log_id": f"log_{uuid.uuid4().hex[:12]}", "operation_type": "SAVE_DRAFT",
            "timestamp": _utcnow(), "operator_id": user.user_id,
            "details": {"document_id": did}})
        return _ok({"document_id": did, "status": "DRAFT", "message": "草稿已保存"})

    def _f(self, rid):
        for fl in _db.risk_flags.values():
            if rid in fl: return fl[rid]
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": f"Risk flag {rid} not found",
            "data": None, "request_id": "req_test"})

    def _log(self, rid, dt, user, comment, **extra):
        entry = {"decision_id": f"d_{uuid.uuid4().hex[:12]}", "decision_type": dt,
                 "reviewer_id": user.user_id, "timestamp": _utcnow(),
                 "comment": comment, **extra}
        _db.decisions.setdefault(rid, []).append(entry)

    def _log_batch(self, did, fids, dt, user):
        for fid in fids:
            self._log(fid, dt, user, "批量确认")

    def _sum(self, did):
        fl = _db.risk_flags.get(did, {})
        hi = [f for f in fl.values() if f["risk_level"] == "HIGH"]
        ap = len([f for f in hi if f["status"] not in ("PENDING_REVIEW",)])
        return {"approved_high_risk": ap, "all_high_risk_resolved": ap >= len(hi)}

    def _high_risk_details(self, flags):
        details = []
        for f in flags.values():
            if f["risk_level"] == "HIGH":
                details.append({
                    "risk_flag_id": f["risk_flag_id"],
                    "clause_type": f["risk_category"],
                    "risk_category": f["risk_category"],
                    "ai_confidence": f["ai_confidence"],
                    "final_status": f["status"],
                    "final_decision": "APPROVE" if f["status"] == "CONFIRMED" else ("EDIT" if f["status"] == "AMENDED" else f["status"]),
                    "reviewer_id": "user_001",
                })
        return details

    @staticmethod
    def _resp(rid, st, summary, **extra):
        d = {"risk_flag_id": rid, "status": st, "decision_id": f"d_{uuid.uuid4().hex[:12]}",
             "updated_review_summary": summary}
        d.update(extra)
        return {"code": 0, "data": d, "message": "success", "request_id": "req_test"}


# ─────────────────────────────────────────────────────────────────
# Mock Report Service (report/export/sign/audit-logs/SSE)
# ─────────────────────────────────────────────────────────────────

class MockReportService:
    async def get_report(self, did, user):
        r = _db.reports.get(did)
        if not r:
            raise HTTPException(status_code=404, detail={
                "code": "NOT_FOUND", "message": "Report not found",
                "data": None, "request_id": "req_test"})
        return _ok(r)

    async def export_report(self, did, fmt, user):
        """Generate a valid PDF report with Chinese text using reportlab."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.lib.enums import TA_CENTER
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import os, tempfile

            # Try to register a Chinese font
            font_name = "Helvetica"
            for fp in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]:
                if os.path.exists(fp):
                    try:
                        pdfmetrics.registerFont(TTFont("CNFont", fp))
                        font_name = "CNFont"
                        break
                    except Exception:
                        continue

            r = _db.reports.get(did)
            if not r:
                raise HTTPException(status_code=404, detail={
                    "code": "NOT_FOUND", "message": "Report not found",
                    "data": None, "request_id": "req_test"})

            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4,
                                    topMargin=25*mm, bottomMargin=25*mm,
                                    leftMargin=25*mm, rightMargin=25*mm)

            title_st = ParagraphStyle("T", fontName=font_name, fontSize=18, leading=26, spaceAfter=8*mm, alignment=TA_CENTER)
            head_st = ParagraphStyle("H", fontName=font_name, fontSize=13, leading=18, spaceBefore=5*mm, spaceAfter=2*mm)
            body_st = ParagraphStyle("B", fontName=font_name, fontSize=11, leading=16, spaceBefore=1*mm, spaceAfter=1*mm)

            story = [Paragraph("NDA 审阅报告", title_st)]
            story.append(Paragraph(f"文档 ID: {did}", body_st))
            story.append(Paragraph(f"生成时间: {r.get('generated_at', 'N/A')}", body_st))
            story.append(Paragraph(f"签署状态: {r.get('sign_status', 'UNSIGNED')}", body_st))
            story.append(Spacer(1, 6*mm))

            agg = r.get("risk_aggregation", {})
            story.append(Paragraph("风险聚合统计", head_st))
            agg_items = [
                f"高风险已确认: {agg.get('high_confirmed', 0)}",
                f"高风险已修正: {agg.get('high_amended', 0)}",
                f"高风险已驳回: {agg.get('high_rejected', 0)}",
                f"中风险自动通过: {agg.get('medium_auto_passed', 0)}",
                f"中风险已审核: {agg.get('medium_reviewed', 0)}",
                f"低风险自动通过: {agg.get('low_auto_passed', 0)}",
                f"低风险已抽查: {agg.get('low_spot_checked', 0)}",
                f"手动补充标记: {agg.get('manual_added', 0)}",
            ]
            for item in agg_items:
                story.append(Paragraph(f"  • {item}", body_st))

            story.append(Spacer(1, 6*mm))
            story.append(Paragraph("审计时间线", head_st))
            for entry in _db.audit_logs[-20:]:
                op = entry.get("operation_type", "?")
                ts = entry.get("timestamp", "")[:19]
                uid = entry.get("operator_id", "?")
                story.append(Paragraph(f"  [{ts}] {op} — {uid}", body_st))

            story.append(Spacer(1, 10*mm))
            story.append(Paragraph("本报告由 AI 审阅系统自动生成，经人工审核后签署生效。", body_st))

            doc.build(story)
            buf.seek(0)
            return StreamingResponse(
                buf, media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="report_{did}.pdf"'})

        except ImportError:
            # Fallback: return a minimal valid PDF
            minimal_pdf = (
                b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
                b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
                b"4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 100 700 Td (Report) Tj ET\nendstream\nendobj\n"
                b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
                b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000272 00000 n \n0000000366 00000 n \n"
                b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n433\n%%EOF"
            )
            return StreamingResponse(
                io.BytesIO(minimal_pdf), media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="report_{did}.pdf"'})

    async def sign_report(self, did, body, user):
        r = _db.reports.get(did)
        if r: r["sign_status"] = "SIGNED"; r["signer_name"] = user.name or user.user_id; r["signed_at"] = _utcnow()
        return _ok({"report_id": f"rpt_{did}", "sign_status": "SIGNED",
                "signer_name": user.name or user.user_id, "signed_at": _utcnow()})

    async def get_audit_logs(self, did, page, size, user):
        logs = _db.audit_logs; t = len(logs); s = (page - 1) * size
        return {"code": 0, "data": {"page": page, "size": size, "total": t,
                "items": logs[s:s+size]}, "message": "success", "request_id": "req_test"}

    async def stream_events(self, did, user):
        async def gen():
            events = [
                ("parse.progress", {"agent_name": "clause_extraction", "progress_pct": 0.3, "current_clause_type": "保密义务"}),
                ("parse.progress", {"agent_name": "clause_extraction", "progress_pct": 0.6, "current_clause_type": "违约救济"}),
                ("parse.progress", {"agent_name": "risk_control", "progress_pct": 0.4, "current_dimension": "赔偿条款"}),
                ("parse.complete", {"document_id": did, "clause_count": 12}),
                ("review.progress", {"agent_name": "risk_control", "clauses_processed": 5, "total_clauses": 12, "current_dimension": "赔偿条款"}),
                ("review.log", {"timestamp": _utcnow(), "agent_name": "risk_control", "message": "发现高风险项：保密期限超过行业标准"}),
                ("review.progress", {"agent_name": "compliance", "clauses_processed": 8, "total_clauses": 12, "current_dimension": "合规检查"}),
                ("review.log", {"timestamp": _utcnow(), "agent_name": "compliance", "message": "合规检查完成，发现3处需要人工审核"}),
                ("review.complete", {"summary": {"high": 3, "medium": 5, "low": 4}}),
                ("interrupt.ready", {"interrupt_id": f"ip_{uuid.uuid4().hex[:8]}", "interrupt_type": "IP-1",
                 "payload": {"risk_flags": list(_db.risk_flags.get(did, {}).values())[:3]}}),
            ]
            for i, (et, d) in enumerate(events):
                import asyncio
                await asyncio.sleep(1.0)  # Simulate realistic delay
                yield f"event: {et}\ndata: {json.dumps(d, ensure_ascii=False)}\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})
