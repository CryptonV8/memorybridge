# MemoryBridge Agent API

FastAPI service providing the Google ADK agent orchestration workflow.

## Structure

```
src/memorybridge_agent/
├── main.py           # FastAPI application, /health and /ready endpoints
├── config.py         # pydantic-settings (reads .env)
├── dependencies.py   # Token auth + ActorContext
├── mcp_client.py     # MCP stdio client — spawns mcp-routines subprocess
├── api/
│   ├── routes.py     # API endpoints
│   └── middleware.py # CorrelationId, RateLimit, ErrorHandling
└── agents/
    ├── workflow.py   # ADK orchestration (plan → safety → communication)
    ├── providers.py  # GeminiProvider / FakeProvider
    └── adk_stubs.py  # ADK integration stubs
```

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Deterministic mode (no Gemini API key required)
export AGENT_PROVIDER=fake
export DATABASE_URL=sqlite:///./test.db

uvicorn src.memorybridge_agent.main:app --port 8000
```

## Environment variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `GOOGLE_API_KEY` | When `AGENT_PROVIDER=gemini` | — | From Secret Manager in production |
| `MEMORYBRIDGE_MODEL` | No | `gemini-2.5-flash` | Not a secret; plain env var |
| `AGENT_PROVIDER` | No | `fake` | `gemini` in production |
| `DATABASE_URL` | Yes (production) | `sqlite:///./test.db` | From Secret Manager in production |
| `LOG_LEVEL` | No | `INFO` | |
| `ENVIRONMENT` | No | `development` | Set to `production` in Cloud Run |

## Production container

```bash
# Build from monorepo root
docker build --file services/agent-api/Dockerfile -t memorybridge-backend .

# Run locally
docker run -p 8080:8080 \
  -e DATABASE_URL="..." \
  -e GOOGLE_API_KEY="..." \
  -e AGENT_PROVIDER=gemini \
  -e MEMORYBRIDGE_MODEL=gemini-2.5-flash \
  -e ENVIRONMENT=production \
  memorybridge-backend
```

## Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | None | Liveness probe |
| `/ready` | GET | None | Readiness probe |
| `/api/routines/interpret` | POST | Bearer | Create routine draft via ADK workflow |
| `/api/routines/{id}/approve` | POST | Bearer | Approve routine draft |
| `/api/routines/{id}` | GET | Bearer | Get routine details |
| `/api/routines/{id}` | PATCH | Bearer | Update routine fields |
| `/api/routines/{id}/reject` | POST | Bearer | Reject routine draft |
| `/api/caregivers/me/routines` | GET | Bearer | List caregiver's routines |
| `/api/caregivers/me/alerts` | GET | Bearer | Get caregiver alerts |
| `/api/users/{id}/today` | GET | Bearer | Get assisted user's today routines |
| `/api/users/{id}/help` | POST | Bearer | Create help alert |
| `/api/users/{id}/contact` | POST | Bearer | Create contact alert |

## Tests

```bash
./.venv/bin/pytest
```
