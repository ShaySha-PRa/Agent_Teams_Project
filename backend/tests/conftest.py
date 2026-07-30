"""
Shared test fixtures, mock services, and test data.

All DB traffic goes through a single in-memory SQLite engine.
The conftest creates tables BEFORE any app code references the engine.
"""

from __future__ import annotations

import hashlib
import io
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os = __import__("os")

# ── Environment (MUST be set before any src imports) ──────────────
_test_storage = os.path.join(os.getcwd(), "storage_test")
os.environ["APP_ENV"] = "staging"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["STORAGE_LOCAL_PATH"] = _test_storage
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:?check_same_thread=False"
os.makedirs(_test_storage, exist_ok=True)

# ── In-Memory SQLite test engine ─────────────────────────────────
_TEST_DB_URL = "sqlite+aiosqlite:///:memory:?check_same_thread=False"
_test_engine = create_async_engine(_TEST_DB_URL, echo=False, future=True)
_test_session_factory = async_sessionmaker(
    bind=_test_engine, class_=AsyncSession, expire_on_commit=False,
)

# ── Create tables NOW, before any src imports ────────────────────
_IMPORTED = False


def _ensure_tables():
    """One-shot: create all tables on the test engine."""
    global _IMPORTED
    if _IMPORTED:
        return
    _IMPORTED = True

    async def _create():
        import models.document   # noqa: F401
        import models.task       # noqa: F401
        import models.clause     # noqa: F401
        import models.risk_flag  # noqa: F401
        import models.playbook   # noqa: F401
        import models.review     # noqa: F401
        import models.audit      # noqa: F401
        import models.interrupt  # noqa: F401
        from models.base import Base
        async with _test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio
    asyncio.run(_create())


_ensure_tables()  # ← tables exist BEFORE any src import


async def get_test_db() -> AsyncSession:
    """Yield a test database session, committing on success."""
    async with _test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── FakeDB ────────────────────────────────────────────────────────

@dataclass
class FakeDB:
    documents: dict[str, dict] = field(default_factory=dict)
    risk_flags: dict[str, dict] = field(default_factory=dict)
    decisions: dict[str, list[dict]] = field(default_factory=dict)
    reports: dict[str, dict] = field(default_factory=dict)
    audit_logs: list[dict] = field(default_factory=list)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_mock_clauses(doc_id: str) -> list[dict]:
    types = [
        "保密义务", "保密期限", "例外情形", "违约救济",
        "存续条款", "管辖法律", "争议解决", "通知条款",
        "可转让性", "完整协议", "保密义务补充", "保密期限补充",
    ]
    return [{
        "clause_id": f"cl_{doc_id}_{i+1:03d}",
        "clause_type": ct,
        "clause_text": f"【{ct}】第{i+1}条测试条款原文。接收方同意对披露方的保密信息予以严格保密...",
        "extraction_confidence": round(0.85 + i * 0.01, 2),
        "page_number": 1 + i // 3,
        "paragraph_number": i + 1,
        "char_offset_start": 1000 + i * 500,
        "char_offset_end": 1200 + i * 500,
        "text_hash": hashlib.sha256(f"clause_{i}".encode()).hexdigest()[:16],
        "source": "AI",
    } for i, ct in enumerate(types)]


def make_mock_risk_flags(doc_id: str, clauses: list[dict]) -> dict[str, dict]:
    risk_data = [
        (0, "HIGH", "合规风险"), (1, "HIGH", "期限不合理"), (3, "HIGH", "财务风险"),
        (2, "MEDIUM", "例外情形不完整"), (4, "MEDIUM", "存续条款不明确"),
        (5, "MEDIUM", "管辖法律不利"), (6, "MEDIUM", "争议解决不公正"),
        (7, "MEDIUM", "通知条款模糊"),
        (8, "LOW", "可转让性"), (9, "LOW", "完整协议"), (10, "LOW", "其他"), (11, "LOW", "其他"),
    ]
    flags = {}
    for idx, (ci, level, cat) in enumerate(risk_data):
        fid = f"rf_{doc_id}_{idx+1:03d}"
        c = clauses[ci] if ci < len(clauses) else clauses[0]
        flags[fid] = {
            "risk_flag_id": fid, "clause_id": c["clause_id"], "document_id": doc_id,
            "risk_level": level, "risk_category": cat,
            "ai_confidence": round(0.75 + idx * 0.02, 2),
            "status": "PENDING_REVIEW" if level == "HIGH" else "UNREVIEWED_AUTO_PASSED",
            "source": "AI_GENERATED",
            "agent_name": "risk_control" if idx % 2 == 0 else "compliance",
            "rationale_text": f"AI: {c['clause_type']}存在{level}风险",
            "playbook_diff_text": "标准: 行业标准\\n实际: 有偏差",
            "regulation_reference": "相关法规", "suggested_wording": "建议修改",
            "clause_location": {"page_number": c["page_number"],
                                "char_offset_start": c["char_offset_start"],
                                "char_offset_end": c["char_offset_end"]},
            "escalated": False, "escalated_from": None, "sampled": level == "LOW",
            "created_at": _utcnow(),
            "created_by": "risk_control_agent" if idx % 2 == 0 else "compliance_agent",
        }
    return flags


# ── Mock Services ─────────────────────────────────────────────────

class BaseMockService:
    def __init__(self, db: FakeDB): self._db = db


class MockReviewService(BaseMockService):
    async def start_review(self, doc_id, user):
        return self._ok({"document_id": doc_id, "review_task_id": f"rt_{doc_id}",
                         "status": "REVIEWING", "thread_id": f"thread_{uuid.uuid4().hex[:8]}",
                         "message": "AI审核已启动"})
    async def pause_review(self, doc_id, user):
        return self._ok({"document_id": doc_id, "paused": True})
    async def resume_review(self, doc_id, user):
        return self._ok({"document_id": doc_id, "paused": False})
    async def cancel_review(self, doc_id, user):
        return self._ok({"document_id": doc_id, "status": "CANCELLED"})
    async def retry_review(self, doc_id, user):
        return self._ok({"document_id": doc_id, "review_task_id": f"rt_{doc_id}_retry",
                         "status": "REVIEWING", "message": "审核重试已启动"})
    async def get_review_summary(self, doc_id, user):
        flags = self._db.risk_flags.get(doc_id, {})
        high = [f for f in flags.values() if f["risk_level"] == "HIGH"]
        appr = len([f for f in high if f["status"] != "PENDING_REVIEW"])
        return self._ok({
            "document_id": doc_id,
            "total_high_risk": len(high), "approved_high_risk": appr,
            "total_medium_risk": len([f for f in flags.values() if f["risk_level"] == "MEDIUM"]),
            "reviewed_medium_risk": 0,
            "low_risk_auto_passed": len([f for f in flags.values() if f["risk_level"] == "LOW"]),
            "manual_added": len([f for f in flags.values() if f["source"] == "MANUALLY_ADDED"]),
            "completion_rate_pct": round(appr / len(high) * 100 if high else 100, 1),
            "all_high_risk_resolved": appr >= len(high),
        })
    @staticmethod
    def _ok(d): return {"code": 0, "message": "success", "data": d, "request_id": "req_test"}


class MockClauseService(BaseMockService):
    async def get_clauses(self, doc_id, user):
        return {"code": 0, "data": {"clauses": make_mock_clauses(doc_id)},
                "message": "success", "request_id": "req_test"}


class MockRiskFlagService(BaseMockService):
    async def get_risk_flags(self, doc_id, level, status_f, category, source, user):
        flags = list(self._db.risk_flags.get(doc_id, {}).values())
        if level: flags = [f for f in flags if f["risk_level"] == level.upper()]
        if status_f: flags = [f for f in flags if f["status"] == status_f]
        if category: flags = [f for f in flags if f["risk_category"] == category]
        if source: flags = [f for f in flags if f["source"] == source]
        return {"code": 0, "data": {"risk_flags": flags}, "message": "success", "request_id": "req_test"}
    async def get_playbook_diff(self, risk_flag_id, user):
        f = self._find_flag(risk_flag_id)
        return {"code": 0, "data": {
            "risk_flag_id": risk_flag_id,
            "playbook_rule": {"playbook_rule_id": "pr_001", "name": "NDA-Rule",
                              "standard_clause_text": "标准", "risk_level": f["risk_level"],
                              "risk_category": f["risk_category"]},
            "match": {"match_type": "PARTIAL", "similarity_score": 0.42,
                      "diff_items": [{"field": "t", "standard_value": "3年", "actual_value": "永久",
                                      "deviation_type": "MISMATCHED"}]}},
            "message": "success", "request_id": "req_test"}
    async def get_decisions(self, risk_flag_id, user):
        return {"code": 0, "data": {"risk_flag_id": risk_flag_id,
                "decisions": self._db.decisions.get(risk_flag_id, [])},
                "message": "success", "request_id": "req_test"}
    def _find_flag(self, rid):
        for fl in self._db.risk_flags.values():
            if rid in fl: return fl[rid]
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": f"Risk flag {rid} not found", "data": None, "request_id": "req_test"})


class MockHITLService(BaseMockService):
    async def approve(self, rid, body, user):
        f = self._f(rid); f["status"] = "CONFIRMED"
        self._log(rid, "APPROVE", user, body.get("comment", ""))
        return self._resp(rid, "CONFIRMED", self._sum(f["document_id"]))
    async def edit(self, rid, body, user):
        f = self._f(rid); c = body.get("comment", "")
        if len(c) < 10:
            raise HTTPException(status_code=422, detail={"code": "VALIDATION_FAILED", "message": "comment must be >= 10 chars", "data": None, "request_id": "req_test"})
        nl = body.get("modified_risk_level")
        if nl and nl not in ("HIGH", "MEDIUM", "LOW"):
            raise HTTPException(status_code=422, detail={"code": "VALIDATION_FAILED", "message": f"Invalid level: {nl}", "data": None, "request_id": "req_test"})
        if nl: f["risk_level"] = nl
        f["status"] = "AMENDED"
        self._log(rid, "EDIT", user, c, modified_risk_level=nl)
        return self._resp(rid, "AMENDED", self._sum(f["document_id"]), modified_risk_level=nl)
    async def reject(self, rid, body, user):
        f = self._f(rid); r = body.get("reject_reason", "")
        if len(r) < 10:
            raise HTTPException(status_code=422, detail={"code": "VALIDATION_FAILED", "message": "reject_reason must be >= 10 chars", "data": None, "request_id": "req_test"})
        f["status"] = "REJECTED"
        self._log(rid, "REJECT", user, r)
        return {"code": 0, "data": {"risk_flag_id": rid, "status": "REJECTED", "decision_id": f"d_{uuid.uuid4().hex[:12]}", "message": "该风险标记已移除"}, "message": "success", "request_id": "req_test"}
    async def batch_approve(self, body, user):
        did = body.get("document_id", ""); fids = body.get("risk_flag_ids", [])
        fl = self._db.risk_flags.get(did, {}); cnt = 0
        for fi in fids:
            if fi in fl: fl[fi]["status"] = "UNREVIEWED_AUTO_PASSED"; cnt += 1
        return {"code": 0, "data": {"batch_approved_count": cnt, "updated_review_summary": {"reviewed_medium_risk": cnt}}, "message": "success", "request_id": "req_test"}
    async def spot_check(self, body, user):
        did = body.get("document_id", ""); r = body.get("sample_ratio", 0.11)
        fl = self._db.risk_flags.get(did, {})
        lo = [f for f in fl.values() if f["risk_level"] == "LOW"]
        n = max(1, int(len(lo) * r)); s = lo[:n]
        return {"code": 0, "data": {"sampled_risk_flags": s, "sample_size": n, "total_low_risk": len(lo), "seed_info": f"sha256({did})[:8]"}, "message": "success", "request_id": "req_test"}
    async def escalate(self, rid, body, user):
        f = self._f(rid); nl = body.get("new_level", "HIGH")
        f["risk_level"] = nl; f["status"] = "ESCALATED_TO_HIGH"
        f["escalated"] = True; f["escalated_from"] = "MEDIUM"
        return {"code": 0, "data": {"risk_flag_id": rid, "new_level": nl, "status": "ESCALATED_TO_HIGH", "message": "已升级为高风险"}, "message": "success", "request_id": "req_test"}
    async def manual_add(self, body, user):
        d = body.get("description", "")
        if len(d) < 10:
            raise HTTPException(status_code=422, detail={"code": "VALIDATION_FAILED", "message": "description must be >= 10 chars", "data": None, "request_id": "req_test"})
        did = body.get("document_id", ""); fid = f"rf_manual_{uuid.uuid4().hex[:12]}"
        nf = {"risk_flag_id": fid, "clause_id": f"cl_manual_{uuid.uuid4().hex[:8]}",
              "document_id": did, "risk_level": body.get("risk_level", "HIGH"),
              "risk_category": body.get("risk_category", "其他"), "ai_confidence": 0.0,
              "status": "PENDING_REVIEW", "source": "MANUALLY_ADDED", "agent_name": "human",
              "rationale_text": d, "playbook_diff_text": "", "regulation_reference": "",
              "suggested_wording": "", "clause_location": body.get("clause_location", {}),
              "escalated": False, "escalated_from": None, "sampled": False,
              "created_at": _utcnow(), "created_by": user.user_id}
        self._db.risk_flags.setdefault(did, {})[fid] = nf
        return {"code": 0, "data": {"risk_flag_id": fid, "clause_id": nf["clause_id"], "risk_level": nf["risk_level"], "status": "PENDING_REVIEW", "source": "MANUALLY_ADDED"}, "message": "success", "request_id": "req_test"}
    async def submit(self, did, body, user):
        flags = self._db.risk_flags.get(did, {})
        unr = [f for f in flags.values() if f["risk_level"] == "HIGH" and f["status"] == "PENDING_REVIEW"]
        if unr:
            raise HTTPException(status_code=409, detail={"code": "CONFLICT", "message": f"仍有 {len(unr)} 项高风险条款待审批", "data": None, "request_id": "req_test"})
        rid = f"rpt_{did}" if not did.startswith("rpt_") else did.replace("d_", "rpt_")
        self._db.reports[did] = {"report_id": rid, "document_id": did, "generated_at": _utcnow(), "sign_status": "UNSIGNED",
            "risk_aggregation": {"high_confirmed": 2, "high_amended": 1, "high_rejected": 0, "medium_auto_passed": 4, "medium_reviewed": 1, "low_auto_passed": 3, "low_spot_checked": 1, "manual_added": 1}}
        return {"code": 0, "data": {"document_id": did, "status": "COMPLETED", "report_id": rid, "message": "审阅已提交，报告生成中"}, "message": "success", "request_id": "req_test"}
    async def save_draft(self, did, body, user):
        return {"code": 0, "data": {"document_id": did, "status": "REVIEWED", "message": "草稿已保存"}, "message": "success", "request_id": "req_test"}

    def _f(self, rid):
        for fl in self._db.risk_flags.values():
            if rid in fl: return fl[rid]
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": f"Risk flag {rid} not found", "data": None, "request_id": "req_test"})

    def _log(self, rid, dt, user, comment, **extra):
        self._db.decisions.setdefault(rid, []).append({"decision_id": f"d_{uuid.uuid4().hex[:12]}", "decision_type": dt, "reviewer_id": user.user_id, "timestamp": _utcnow(), "comment": comment, **extra})

    def _sum(self, did):
        fl = self._db.risk_flags.get(did, {})
        hi = [f for f in fl.values() if f["risk_level"] == "HIGH"]
        ap = len([f for f in hi if f["status"] != "PENDING_REVIEW"])
        return {"approved_high_risk": ap, "all_high_risk_resolved": ap >= len(hi)}

    @staticmethod
    def _resp(rid, st, summary, **extra):
        d = {"risk_flag_id": rid, "status": st, "decision_id": f"d_{uuid.uuid4().hex[:12]}", "updated_review_summary": summary}
        d.update(extra)
        return {"code": 0, "data": d, "message": "success", "request_id": "req_test"}


class MockReportService(BaseMockService):
    async def get_report(self, did, user):
        r = self._db.reports.get(did)
        if not r:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Report not found", "data": None, "request_id": "req_test"})
        return {"code": 0, "data": r, "message": "success", "request_id": "req_test"}
    async def export_report(self, did, fmt, user):
        return StreamingResponse(io.BytesIO(b"%PDF-1.4\n%Report"), media_type="application/pdf",
                                 headers={"Content-Disposition": f'attachment; filename="report_{did}.pdf"'})
    async def sign_report(self, did, body, user):
        r = self._db.reports.get(did)
        if r: r["sign_status"] = "SIGNED"
        return {"code": 0, "data": {"report_id": f"rpt_{did}", "sign_status": "SIGNED", "signer_name": user.name or user.user_id, "signed_at": _utcnow()}, "message": "success", "request_id": "req_test"}
    async def get_audit_logs(self, did, page, size, user):
        logs = self._db.audit_logs; t = len(logs); s = (page - 1) * size
        return {"code": 0, "data": {"page": page, "size": size, "total": t, "items": logs[s:s+size]}, "message": "success", "request_id": "req_test"}
    async def stream_events(self, did, user):
        async def gen():
            for et, d in [
                ("parse.progress", {"agent_name": "clause_extraction", "progress_pct": 0.6}),
                ("parse.complete", {"document_id": did, "clause_count": 12}),
                ("review.progress", {"agent_name": "risk_control", "clauses_processed": 8, "total_clauses": 20}),
                ("review.log", {"timestamp": _utcnow(), "agent_name": "risk_control", "message": "发现高风险项"}),
                ("review.complete", {"summary": {"high": 3, "medium": 5, "low": 4}}),
            ]:
                yield f"event: {et}\ndata: {json.dumps(d)}\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def fake_db() -> FakeDB:
    return FakeDB()


@pytest.fixture
def test_app(fake_db: FakeDB):
    """Build test FastAPI app. Tables already exist on _test_engine.
    Force src.core.database to use the test engine."""
    import src.core.database as _db
    _db.engine = _test_engine
    _db.async_session_factory = _test_session_factory

    from src.core.config import get_settings
    get_settings.cache_clear()

    from src.main import create_app
    app = create_app()

    # DB dependency
    app.dependency_overrides[_get_db_from_module()] = get_test_db

    # Auth dependency
    from core.security import get_current_user, CurrentUser
    async def test_get_current_user(
        authorization: str | None = __import__("fastapi").Header(default=None),
    ) -> CurrentUser:
        if authorization is None:
            raise __import__("fastapi").HTTPException(status_code=401, detail="Authorization required")
        if authorization.startswith("Bearer "):
            return CurrentUser(user_id="test-user-001", name="Test User")
        raise __import__("fastapi").HTTPException(status_code=401, detail="Bearer token required")
    app.dependency_overrides[get_current_user] = test_get_current_user

    # Mock DI services
    _install_di_overrides(app, fake_db)
    return app


def _get_db_from_module():
    from core.database import get_db
    return get_db


def _install_di_overrides(app: FastAPI, fake_db: FakeDB):
    from api.routes.review import get_review_service, get_clause_service, get_risk_flag_service
    from api.routes.hitl import get_hitl_service
    from api.routes.reports import get_report_service
    app.dependency_overrides[get_review_service] = lambda: MockReviewService(fake_db)
    app.dependency_overrides[get_clause_service] = lambda: MockClauseService(fake_db)
    app.dependency_overrides[get_risk_flag_service] = lambda: MockRiskFlagService(fake_db)
    app.dependency_overrides[get_hitl_service] = lambda: MockHITLService(fake_db)
    app.dependency_overrides[get_report_service] = lambda: MockReportService(fake_db)


@pytest.fixture
def auth_headers() -> dict:
    return {"Authorization": "Bearer test-jwt-token"}


@pytest.fixture
async def async_client(test_app: FastAPI):
    transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def get_doc_id(data: dict) -> str:
    return data.get("document_id") or data.get("id", "")


# ── Sample Files ──────────────────────────────────────────────────

@pytest.fixture(scope="session")
def sample_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>"
        b"/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 44>>stream\n"
        b"BT /F1 12 Tf 50 750 Td (NDA Test Document) Tj ET\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        b"0000000115 00000 n \n0000000280 00000 n \n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n360\n%%EOF"
    )


@pytest.fixture(scope="session")
def sample_docx_bytes() -> bytes:
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('mimetype', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    return buf.getvalue()


@pytest.fixture(scope="session")
def sample_encrypted_pdf() -> bytes:
    return (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"4 0 obj<</Filter/Standard/V 2/R 3/O<...>/U<...>/P -4/EncryptMetadata true>>endobj\n"
            b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
            b"0000000115 00000 n \n0000000170 00000 n \n"
            b"trailer<</Size 5/Root 1 0 R/Encrypt 4 0 R>>\nstartxref\n250\n%%EOF")


@pytest.fixture(scope="session")
def sample_corrupted_pdf() -> bytes:
    return b"%PDF-1.4\n%%This is corrupted\n\x00\xFF"


@pytest.fixture(scope="session")
def sample_unsupported_file() -> bytes:
    return b"Hello, this is a plain text file."


# ── Stateful Fixtures ─────────────────────────────────────────────

@pytest.fixture
async def uploaded_document_id(
    async_client: httpx.AsyncClient, auth_headers: dict, sample_pdf_bytes: bytes,
) -> str:
    resp = await async_client.post(
        "/api/v1/documents/upload",
        files={"file": ("test-nda.pdf", sample_pdf_bytes, "application/pdf")},
        data={"title": "Test NDA Document", "document_type": "NDA"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, f"Upload failed: {resp.text}"
    return get_doc_id(resp.json()["data"])


@pytest.fixture
async def parsed_document_id(
    async_client: httpx.AsyncClient, auth_headers: dict,
    uploaded_document_id: str, fake_db: FakeDB,
) -> str:
    doc_id = uploaded_document_id
    fake_db.risk_flags.setdefault(doc_id, make_mock_risk_flags(doc_id, make_mock_clauses(doc_id)))
    return doc_id


@pytest.fixture
async def reviewed_document_id(
    async_client: httpx.AsyncClient, auth_headers: dict,
    parsed_document_id: str, fake_db: FakeDB,
) -> str:
    doc_id = parsed_document_id
    fake_db.risk_flags.setdefault(doc_id, make_mock_risk_flags(doc_id, make_mock_clauses(doc_id)))
    return doc_id


@pytest.fixture
def risk_flag_ids(fake_db: FakeDB, reviewed_document_id: str) -> dict[str, list[str]]:
    flags = fake_db.risk_flags.get(reviewed_document_id, {})
    result: dict[str, list[str]] = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for fid, flag in flags.items():
        level = flag.get("risk_level", "LOW")
        if level in result:
            result[level].append(fid)
    return result
