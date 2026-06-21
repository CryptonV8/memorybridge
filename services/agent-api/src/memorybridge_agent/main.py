import logging
from fastapi import FastAPI
from .api.middleware import CorrelationIdMiddleware, ErrorHandlingMiddleware
from .api.routes import router as api_router
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="MemoryBridge Agent API",
    description="Intelligent routing and workflow service powered by Google ADK",
    version="0.1.0"
)

# Add Middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# Include Routers
app.include_router(api_router)

@app.get("/health")
async def root_health_check():
    return {"status": "ok"}

@app.get("/ready")
async def root_readiness_check():
    return {"status": "ready"}

# OpenTelemetry Instrumentation
FastAPIInstrumentor.instrument_app(app)
