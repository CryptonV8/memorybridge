import logging
import os
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .api.middleware import CorrelationIdMiddleware, ErrorHandlingMiddleware, RateLimitMiddleware
from .api.routes import router as api_router
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stdout,
)

app = FastAPI(
    title="MemoryBridge Agent API",
    description="Intelligent routing and workflow service powered by Google ADK",
    version="0.1.0",
    # Disable interactive docs in production to reduce attack surface
    docs_url="/docs" if os.environ.get("ENVIRONMENT", "development") != "production" else None,
    redoc_url=None,
)

# Add Middleware — outermost first (ErrorHandling → RateLimit → CorrelationId → route)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CorrelationIdMiddleware)


# Include Routers
app.include_router(api_router)


@app.get("/health", summary="Liveness probe", tags=["ops"])
async def root_health_check():
    """Returns 200 when the process is running. Safe to call publicly."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "service": "memorybridge-backend"},
    )


@app.get("/ready", summary="Readiness probe", tags=["ops"])
async def root_readiness_check():
    """
    Verifies essential dependencies before accepting traffic:
    - Configuration loaded (GOOGLE_API_KEY or AGENT_PROVIDER=fake present)
    - DATABASE_URL configured
    - MCP server script is locatable on disk

    Does NOT make a live Gemini generation request.
    Does NOT expose secrets, connection strings, or stack traces.
    """
    from .config import settings
    issues = []

    # 1. Configuration check
    if settings.agent_provider == "gemini" and not settings.google_api_key:
        issues.append("GOOGLE_API_KEY not configured for gemini provider")

    # 2. Database URL present (not validated for connectivity — that is the seed script's job)
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        issues.append("DATABASE_URL not configured")

    # 3. MCP subprocess script locatable
    import os as _os
    mcp_client_path = _os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)),
        "..", "..", "..", "..", "mcp-routines", "src", "server.py"
    )
    mcp_resolved = _os.path.normpath(mcp_client_path)
    if not _os.path.exists(mcp_resolved):
        issues.append("MCP server script not found at expected path")

    if issues:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "memorybridge-backend",
                "issues": issues,
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "ready",
            "service": "memorybridge-backend",
            "provider": settings.agent_provider,
        },
    )


# OpenTelemetry Instrumentation
FastAPIInstrumentor.instrument_app(app)
