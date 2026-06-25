# =====================================================================
# MemoryBridge — Backend Dockerfile
# Packages FastAPI Agent API + MCP Routines server in a single image.
# The MCP server runs as a local subprocess over stdio (no network port).
# =====================================================================

# ── Stage 1: Builder ──────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Install build tools only in the builder stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# ── Install agent-api dependencies ────────────────────────────────────
COPY services/agent-api/pyproject.toml /build/agent-api/
# Install only runtime deps (no dev extras)
RUN pip install --no-cache-dir --prefix=/install \
    "fastapi>=0.111.0" \
    "uvicorn>=0.30.1" \
    "pydantic>=2.7.1" \
    "pydantic-settings>=2.2.1" \
    "google-genai>=2.0.0" \
    "google-adk>=1.0.0" \
    "mcp>=1.0.0" \
    "opentelemetry-api>=1.24.0" \
    "opentelemetry-sdk>=1.24.0" \
    "opentelemetry-instrumentation-fastapi>=0.45b0" \
    "httpx>=0.27.0"

# ── Install mcp-routines dependencies ─────────────────────────────────
COPY services/mcp-routines/requirements.txt /build/mcp-routines/
RUN pip install --no-cache-dir --prefix=/install \
    "SQLAlchemy==2.0.30" \
    "alembic==1.13.1" \
    "pydantic==2.13.4" \
    "psycopg2-binary==2.9.9" \
    "python-dateutil==2.9.0.post0" \
    "mcp==1.28.0"

# ── Stage 2: Runtime ──────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Install only libpq runtime (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --no-create-home --shell /bin/false appuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# ── Copy application source ───────────────────────────────────────────
# Agent API
COPY services/agent-api/src /app/services/agent-api/src

# MCP Routines server (started as subprocess by mcp_client.py)
COPY services/mcp-routines/src /app/services/mcp-routines/src
COPY services/mcp-routines/alembic /app/services/mcp-routines/alembic
COPY services/mcp-routines/alembic.ini /app/services/mcp-routines/alembic.ini

# Agent Skills (loaded by skill-aware agents at runtime)
COPY .agent /app/.agent

# ── Environment ───────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Point mcp_client.py at the embedded mcp-routines location
    MCP_ROUTINES_DIR=/app/services/mcp-routines \
    PYTHONPATH=/app/services/agent-api/src:/app/services/mcp-routines

# Cloud Run injects PORT; Uvicorn listens on it.
ENV PORT=8080

USER appuser

# ── Health check (Docker/Cloud Run will also use /health endpoint) ────
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# ── Entrypoint ────────────────────────────────────────────────────────
# Uvicorn starts the FastAPI app.
# The MCP server is spawned as a subprocess by mcp_client.py on demand
# (stdio transport — no extra network port required).
CMD ["sh", "-c", "exec uvicorn memorybridge_agent.main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 1 \
    --log-level info \
    --no-access-log"]
