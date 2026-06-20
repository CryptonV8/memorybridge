# Architecture Plan

## 1. System Overview
MemoryBridge is organized as a monorepo containing three primary applications:
1. **Next.js Web Interface** (`apps/web`): Dual-mode interface serving both Caregiver and Assisted User views.
2. **FastAPI Agent Service** (`services/agent-api`): The intelligent routing layer powered by Google ADK.
3. **MCP Routines Server** (`services/mcp-routines`): A sandboxed server enforcing deterministic data persistence into Neon PostgreSQL.

## 2. Request and Data Flow
**Routine Creation Flow:**
1. Caregiver inputs natural language text via the Next.js UI.
2. Next.js calls `POST /api/routines/interpret` on the FastAPI Agent Service.
3. Root Orchestrator invokes the **Routine Planning Agent** to extract JSON.
4. Output passes to the **Safety Policy Agent** for deterministic and semantic checks.
5. If allowed, output passes to the **Communication Agent** for UI copy generation.
6. The service stores a draft via the MCP Server's `create_routine_draft` tool.
7. Next.js displays the draft to the Caregiver.

**Approval Flow:**
1. Caregiver reviews the draft, including the safety reasoning and rewritten text.
2. Caregiver clicks "Approve". Next.js calls `POST /api/routines/{id}/approve`.
3. Agent Service routes to the MCP Server's `approve_routine` tool.
4. Tool verifies caregiver role and safety decision, activates routine, and appends an audit event.

**Delivery and Task Completion Flow:**
1. Assisted user views `/today`. UI polls `get_today_routines` from the MCP server.
2. User taps "Done". UI calls `POST /api/routines/{id}/status` with `completed`.
3. MCP Server updates status and fires an audit event.

**Help Escalation Flow:**
1. Assisted user taps "Help me".
2. Next.js triggers the **Escalation Agent**.
3. Agent uses the `create_caregiver_alert` MCP tool.
4. Caregiver sees the alert in the app dashboard.

## 3. Database Migration Plan
We will use Alembic (Python) alongside Neon PostgreSQL. 
* **V1:** Initial schema creation (`users`, `assisted_user_profiles`, `caregiver_relationships`).
* **V2:** Routine storage (`routines`, `routine_events`).
* **V3:** Alerting and auditing (`caregiver_alerts`, `audit_events`).
Migration scripts will be strictly versioned in `infra/database/migrations`. The agent never runs migrations directly; they are executed via CI/CD.

## 4. Dependencies
**Pinned Versions:**
* **Next.js:** `14.2.3`
* **React:** `18.3.1`
* **Tailwind CSS:** `3.4.3`
* **Python:** `3.11`
* **FastAPI:** `0.111.0`
* **Uvicorn:** `0.30.1`
* **Pydantic:** `2.13.4`
* **SQLAlchemy:** `2.0.30`
* **Alembic:** `1.13.1`
* **Google ADK / google-genai:** `0.5.0`
* **MCP SDK:** `1.28.0`
* **asyncpg:** `0.29.0`


## 5. Sequence of Implementation Milestones
* **Phase 0:** Planning and Scaffold (Current)
* **Phase 1:** Deterministic Core (DB migrations, MCP server, unit tests)
* **Phase 2:** Agent Workflow (ADK routing, skills, agents, schema validation)
* **Phase 3:** Caregiver UI (Drafting, approval, audit viewing)
* **Phase 4:** Assisted User UI (Today view, text-to-speech, completion, help)
* **Phase 5:** Evaluation & Hardening (Run eval datasets, accessibility checks, SAST)
* **Phase 6:** Deployment & Submission (Cloud Run, Kaggle write-up)

## 6. Ambiguities & Proposed Resolutions
* **Timezones:** Input does not mandate how user timezone vs caregiver timezone is reconciled. **Resolution:** Enforce a single timezone field per routine derived from the assisted user profile, verified by the Planning Agent.
* **Text-to-speech Implementation:** The spec mentions "optional text-to-speech" but no specific API. **Resolution:** We will rely exclusively on the browser's native `SpeechSynthesis` Web API to keep the application boundary restricted and avoid third-party TTS service complexity.
* **Caregiver Alert Delivery:** The spec says "in-app caregiver alert" but doesn't specify realtime. **Resolution:** Polling via Next.js SWR/React Query for simplicity; no WebSockets required for the MVP.
