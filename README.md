# MemoryBridge: Safe Daily Routine and Caregiver Support Agent

> **Demo only. Synthetic data. Not a medical device.**

MemoryBridge is a safety-first assistive prototype for people living with early-stage dementia and the family members or caregivers who support them.

---

## 1. System Overview

MemoryBridge is a monorepo containing three core components:

1. **Next.js Web Interface** (`apps/web`): Portal for caregivers to create, edit, and approve daily routines; accessible `/today` view for the assisted user.
2. **FastAPI Agent Service** (`services/agent-api`): Multi-agent orchestration via Google ADK (routine planning → safety policy → dementia-friendly communication → human approval).
3. **MCP Routines Server** (`services/mcp-routines`): Model Context Protocol server executing deterministic database operations over Neon PostgreSQL via stdio transport.

**Demo personas:** Anna Petrova (caregiver) and Maria Petrova (assisted user).

---

## 2. Security Design

- **Cookie-Based Sessions:** Caregivers authenticate via a signed, encrypted server-side session cookie (`iron-session`).
- **HttpOnly & Secure:** Session cookies are `HttpOnly`, `SameSite=Lax`, and `Secure` in production.
- **Server API Boundary:** All backend calls are proxied server-side by Next.js. The browser never receives the backend token.
- **MCP Context Injection:** The `_context` parameter (actor ID, role, correlation ID) is injected by the FastAPI gateway — the LLM cannot supply or modify it.
- **Human-in-the-Loop:** No routine becomes active without explicit caregiver approval.

---

## 3. Local Development Setup

### Step 1: Set up environment variables

```bash
cp .env.example .env
# Fill in DATABASE_URL, GOOGLE_API_KEY, SESSION_SECRET, etc.
```

### Step 2: Database setup (MCP Routines)

```bash
cd services/mcp-routines
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed synthetic demo data
python ../../scripts/seed_demo_data.py
```

### Step 3: Start FastAPI Agent Service

```bash
cd services/agent-api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

uvicorn src.memorybridge_agent.main:app --port 8000
```

Set `AGENT_PROVIDER=fake` in `.env` for deterministic local mode (no Gemini API key required).

### Step 4: Start Next.js Web App

```bash
cd apps/web
npm install
npm run dev -- -p 3000
```

---

## 4. Running Tests

```bash
# MCP Routines unit tests
cd services/mcp-routines
PYTHONPATH=. ./venv/bin/pytest

# Agent API tests
cd services/agent-api
./.venv/bin/pytest

# Web unit tests (Jest + axe accessibility)
cd apps/web
npm test

# E2E tests (requires TEST_DATABASE_URL set)
cd apps/web
npx playwright test
```

---

## 5. Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full Cloud Run deployment guide.

Quick reference:

```bash
# 1. Migrate database
./infra/cloudrun/migrate.sh

# 2. Seed demo data
./infra/cloudrun/seed.sh

# 3. Deploy backend (private)
./infra/cloudrun/deploy-backend.sh --project PROJECT --region REGION

# 4. Deploy web (public)
./infra/cloudrun/deploy-web.sh --project PROJECT --region REGION --backend-url BACKEND_URL

# 5. Smoke check
./infra/cloudrun/smoke-check.sh --web-url WEB_URL --backend-url BACKEND_URL
```

---

## 6. Evaluation

```bash
cd scripts
AGENT_PROVIDER=fake PYTHONPATH=../services/agent-api/src \
  python run_evals.py
```

---

## 7. Accessibility

MemoryBridge targets WCAG 2.2 AA. Key features:
- Skip navigation link as first keyboard focus target.
- Minimum 44 × 44 px interactive targets on the `/today` view.
- Color contrast meets AA ratios.
- Text-to-speech for routine instructions.
- axe-core: 0 violations in automated tests.

---

## 8. Limitations and Responsible Use

- **MVP Sandbox:** Synthetic data only. No SMS, email, or emergency services.
- **Not a medical device:** Does not diagnose dementia, recommend treatment, or manage medication.
- **Rate limiter:** In-memory (per-instance). For production multi-instance deployments, replace with Redis.
- **Demo auth:** Session-based with static tokens. For production, replace with a proper OAuth/OIDC provider.
- **Agent Engine:** Not deployed in this phase. See `specs/ARCHITECTURE.md` for future work notes.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) and [docs/ROLLBACK.md](docs/ROLLBACK.md) for operational procedures.
