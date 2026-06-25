# MemoryBridge MCP Routines Server

Model Context Protocol (MCP) server providing deterministic database operations over Neon PostgreSQL. Started as a subprocess by the FastAPI Agent API via stdio transport.

## Architecture

```
services/mcp-routines/
├── src/
│   ├── server.py     # MCP stdio server entry point
│   ├── mcp_server.py # Business logic (tool implementations)
│   ├── database.py   # SQLAlchemy engine + session factory
│   ├── models.py     # SQLAlchemy ORM models
│   ├── schemas.py    # Pydantic schemas (strict validation)
│   ├── auth.py       # Role + ownership checks
│   └── safety.py     # Deterministic keyword safety policy
├── alembic/          # Database migrations
└── requirements.txt  # Pinned runtime dependencies
```

## MCP transport

The server uses **stdio transport**. It is started as a subprocess by `mcp_client.py` in the agent-api service. It does **not** listen on a network port and is not deployed as a separate Cloud Run service.

## Environment variables

| Variable | Default | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `sqlite:///./test.db` | Neon pooled URL in production |
| `MIGRATION_DATABASE_URL` | Fallback to `DATABASE_URL` | Neon direct/unpooled URL for Alembic |

## Local setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run migrations
export DATABASE_URL="postgresql://..."
alembic upgrade head

# Verify revision
alembic current
```

## Available MCP tools

| Tool | Role required | Description |
|------|--------------|-------------|
| `get_user_preferences` | any | Get assisted user's approved preferences |
| `create_routine_draft` | caregiver | Create a non-active routine draft |
| `approve_routine` | caregiver | Activate an approved draft |
| `get_today_routines` | any | Get today's active routines |
| `mark_routine_status` | assisted_user | Mark routine as completed/help/missed |
| `create_caregiver_alert` | assisted_user | Create in-app alert (no external notifications) |
| `get_approved_contacts` | any | Get approved contact list |
| `get_routine` | any | Get a single routine by ID |
| `update_routine` | caregiver | Update routine details (resets approval) |
| `reject_routine` | caregiver | Reject a pending draft |
| `list_caregiver_routines` | caregiver | List all routines for caregiver's users |
| `get_audit_events` | caregiver | Get audit timeline for a correlation ID |
| `get_caregiver_alerts` | caregiver | Get all alerts for caregiver |

## Tests

```bash
PYTHONPATH=. ./venv/bin/pytest
```

## Neon PostgreSQL pool settings

Runtime pool settings (from `database.py`):

```
pool_pre_ping=True    # Drop stale connections (Neon times out idle)
pool_size=2           # Small pool for Cloud Run
max_overflow=3        # Allow short bursts
pool_recycle=1800     # Recycle every 30 minutes
pool_timeout=30       # Raise after 30s if no connection available
sslmode=require       # Enforced automatically if not in URL
```
