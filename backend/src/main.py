"""
FastAPI application factory for Agent Smart Document Review System.
"""

from __future__ import annotations

import uuid
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import get_settings
from core.database import engine
from core.exceptions import AppException
from models.base import Base
import models  # noqa: F401 — ensure all ORM models are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks.

    - Startup: create all DB tables (dev mode), initialise settings.
    - Shutdown: dispose the async engine.
    """
    settings = get_settings()
    if settings.APP_ENV == "development" and not os.environ.get("DATABASE_URL", "").startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Any):
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Convert FastAPI HTTPException to standard response envelope."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": getattr(exc, "code", "INTERNAL_ERROR") if not isinstance(exc.detail, dict) else exc.detail.get("code", "INTERNAL_ERROR"),
                "message": str(exc.detail) if not isinstance(exc.detail, dict) else exc.detail.get("message", str(exc.detail)),
                "data": None,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "code": exc.code.value,
                "message": exc.message,
                "data": None,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Catch-all handler to return a consistent error envelope."""
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": str(exc) if settings.DEBUG else "Internal server error",
                "data": None,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    # Register API routers
    from api import router as api_router
    app.include_router(api_router)

    return app


app: FastAPI = create_app()
