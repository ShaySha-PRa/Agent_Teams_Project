# Backend Dockerfile — FastAPI + SQLAlchemy + LangGraph
# Multi-stage: builder for deps, final for runtime

FROM python:3.12-slim AS builder

WORKDIR /app

# Install system deps for reportlab PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir --user \
    fastapi>=0.115.0 \
    "uvicorn[standard]>=0.32.0" \
    sse-starlette>=2.1.0 \
    python-multipart>=0.0.18 \
    "sqlalchemy[asyncio]>=2.0.35" \
    aiosqlite \
    alembic>=1.14.0 \
    pydantic>=2.9.0 \
    pydantic-settings>=2.6.0 \
    python-dotenv>=1.0.0 \
    "python-jose[cryptography]" \
    reportlab \
    langchain-openai \
    langchain \
    langgraph \
    fastapi-cors

# Final stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed deps from builder
COPY --from=builder /root/.local /root/.local

# Ensure local bin is on PATH
ENV PATH=/root/.local/bin:$PATH

# Copy backend source
COPY backend/src/ ./src/

# Copy .env.example as default
COPY backend/.env.example ./.env

# Copy pyproject for reference
COPY backend/pyproject.toml .

# Storage directory for uploaded files
RUN mkdir -p /app/storage

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/dashboard/stats')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
