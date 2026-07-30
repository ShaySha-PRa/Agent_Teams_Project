"""Master API router — mounts all sub-routers under /api/v1.

Sub-routers live in api/routes/ and follow the API spec groups:
- documents: upload, list, detail, file, parse, retry
- review: AI review control + query (clauses, risk-flags, decisions, summary)
- hitl: 8 human-in-the-loop operations (approve/edit/reject/batch/sample/escalate/manual/submit)
- reports: report, export, sign, audit-logs, SSE, dashboard, playbooks
"""

from fastapi import APIRouter

from api.routes.documents import router as documents_routes
from api.routes.review import router as review_routes
from api.routes.hitl import router as hitl_routes
from api.routes.reports import router as reports_routes

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(documents_routes, tags=["Documents"])
api_v1_router.include_router(review_routes, tags=["Review"])
api_v1_router.include_router(hitl_routes, tags=["HITL"])
api_v1_router.include_router(reports_routes, tags=["Reports"])
