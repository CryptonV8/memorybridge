# MemoryBridge: Safe Daily Routine and Caregiver Support Agent

MemoryBridge is a safety-first assistive prototype application tailored for people living with early-stage dementia, alongside the family members or caregivers who support them.

---

## 1. System Overview

MemoryBridge is designed as a monorepo containing three core components:
1. **Next.js Web Interface** (`apps/web`): Portal for Caregivers to create, edit, revalidate, and approve daily routines.
2. **FastAPI Agent Service** (`services/agent-api`): An orchestration layer using Google ADK to run safe daily routine interpretation workflows.
3. **MCP Routines Server** (`services/mcp-routines`): A Model Context Protocol server executing deterministic database updates and policy checks over Neon PostgreSQL.

---

## 2. Server-Only Session & Token Isolation Design

To prevent security risks and guarantee that the upstream `DEMO_CAREGIVER_TOKEN` is never sent to the browser:
- **Cookie-Based Sessions:** The web interface authenticates caregivers via a signed, encrypted server-side session cookie (`iron-session`).
- **HttpOnly & Secure:** The session cookie is configured as `HttpOnly`, `SameSite=Lax` or stricter, and `Secure` in production, blocking client-side JavaScript access.
- **Server API Boundary:** The Next.js server actions act as the exclusive boundary to the backend FastAPI Agent Service. All requests are proxied server-side, attaching the `DEMO_CAREGIVER_TOKEN` only on authorized server processes. The browser never receives this token.

---

## 3. Local Service Startup Order

To run MemoryBridge locally, start the services in this exact order:

### Step 1: PostgreSQL Database Setup
Ensure PostgreSQL is running and seed the database schemas. Inside `services/mcp-routines`:
```bash
# Recreate virtual env and install requirements
uv venv venv --python 3.11
source venv/bin/activate
uv pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed synthetic demo data (Anna Petrova & Maria Petrova)
export DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"
python ../../scripts/seed_demo_data.py
```

### Step 2: Start FastAPI Agent Service (Gateway)
Starts the gateway server on port 8000. It communicates with the MCP server on-demand via stdio transport. Inside `services/agent-api`:
```bash
# Setup virtual env
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt

# Run API server (Uvicorn)
uvicorn src.memorybridge_agent.main:app --port 8000
```
*Note: To run in developer/testing mode, configure `AGENT_PROVIDER=fake` in `.env.local` to use the deterministic fake-model provider.*

### Step 3: Start Next.js Web Application
Starts the frontend dashboard on port 3000. Inside `apps/web`:
```bash
# Install NPM dependencies
npm install

# Run the Next.js dev server
npm run dev -- -p 3000
```

---

## 4. Test Commands

MemoryBridge has multi-tier tests verifying formatting, types, APIs, security, and UI flows.

### Gateway and MCP Service Tests (Python):
Run pytest inside `services/agent-api` and `services/mcp-routines` to test logic and schemas.
```bash
# Agent-API Tests
cd services/agent-api
./.venv/bin/pytest

# MCP Server Tests
cd services/mcp-routines
PYTHONPATH=. ./venv/bin/pytest
```

### Frontend Unit & Security Tests (Jest):
Run Jest tests verifying layout rendering, state filters, and client bundle token non-exposure.
```bash
cd apps/web
npm test
```

### End-to-End Tests (Playwright):
Run Playwright integration test suite covering the entire user flow in deterministic fake-model mode.
```bash
cd apps/web
npx playwright test
```

---

## 5. Visual Screenshot Generation

To visually verify responsive layouts across Desktop (1440x900), Tablet (768x1024), and Mobile (390x844):
- Screenshots are automatically captured by Playwright during the E2E test runs.
- Visual files are written to the artifacts directory, including `login`, `dashboard`, `new_routine`, and `filled_routine_form` layouts.

---

## 6. Accessibility Audits

MemoryBridge targets WCAG 2.2 AA. Verify accessibility manually or via automated checks:
- Skip navigation link is accessible as the first keyboard focus target.
- Color contrast meets standard ratios.
- Inputs, checkboxes, and buttons feature visible focus outline indicators.
- Interactive targets support a minimum size of 44 × 44 pixels.

---

## 7. Project Limitations & Phasing

- **MVP Sandbox:** Synthetic datasets only. SMS, email, telephone, or live emergency services are NOT implemented.
- **Phase 4 Status:** Phase 4 (Assisted User `/today` interface and live Text-to-Speech) has not started. All current changes are restricted to Phase 3.
