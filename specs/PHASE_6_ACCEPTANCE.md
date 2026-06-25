# Phase 6 Acceptance Report — MemoryBridge

**Gate:** Phase 6 — Deployment and Public Demo Preparation
**Date:** 2026-06-25
**Evaluator:** Antigravity (automated)
**Decision: PASS WITH DOCUMENTED LIMITATIONS** *(preparation stage complete — deployment pending user approval)*

---

## Phase 5 Formal Acceptance Gate

Phase 5 is **formally accepted** before proceeding.

- **Phase 5 decision:** PASS WITH DOCUMENTED LIMITATIONS
- **Reference:** `specs/PHASE_5_ACCEPTANCE.md`
- **All Phase 5 objectives met:** Evaluations, security hardening, accessibility tests, prompt-injection tests, SAST, and rate limiting are complete.
- **Open Phase 5 limitation (L-01):** Capstone E2E BLOCKED on PostgreSQL — this is resolved by Phase 6 database deployment.

---

## 1. Final Deployment Architecture

```text
Public Cloud Run service: memorybridge-web
  - Next.js 16 standalone output
  - Server-side iron-session caregiver authentication
  - Server-side calls to private backend (never browser-direct)
  - AGENT_API_BASE_URL injected at runtime (not in client bundle)
  - Secrets: SESSION_SECRET, DEMO_CAREGIVER_TOKEN, DEMO_ASSISTED_USER_TOKEN

Private Cloud Run service: memorybridge-backend
  - FastAPI 0.111+ Agent API
  - Google ADK 2.3.x multi-agent workflow
  - MCP Routines server started as local subprocess over stdio
  - Database access only through MCP domain layer
  - Secrets: DATABASE_URL, GOOGLE_API_KEY

External managed database: Neon PostgreSQL
  - Project: MemoryBridge
  - Runtime URL: pooled (DATABASE_URL)
  - Migration URL: direct/unpooled (MIGRATION_DATABASE_URL)
  - SSL enforced on all connections
```

---

## 2. Container Image Inventory

| Image | Source Dockerfile | Base | Non-root user | Standalone |
|-------|-------------------|------|--------------|-----------|
| `memorybridge/backend:TAG` | `services/agent-api/Dockerfile` | `python:3.11-slim` | `appuser` (uid 1001) | N/A |
| `memorybridge/web:TAG` | `apps/web/Dockerfile` | `node:20-alpine` | `nextjs` (uid 1001) | Yes (`output: "standalone"`) |

---

## 3. Google Cloud Project and Region

| Parameter | Value |
|-----------|-------|
| `GOOGLE_CLOUD_PROJECT` | *Set by user before deployment* |
| `GOOGLE_CLOUD_REGION` | *Set by user before deployment* |
| Artifact Registry | `REGION-docker.pkg.dev/PROJECT/memorybridge` |

---

## 4. Cloud Run Service Names

| Service | Visibility | Service Account |
|---------|-----------|----------------|
| `memorybridge-web` | Public (`--allow-unauthenticated`) | `memorybridge-web-sa` |
| `memorybridge-backend` | Private (`--no-allow-unauthenticated`) | `memorybridge-backend-sa` |

---

## 5. Neon Database Configuration Status

| Item | Status |
|------|--------|
| Neon project | Existing (MemoryBridge) — not created or destroyed |
| DATABASE_URL (pooled) | Pending — user must supply from Neon Console |
| MIGRATION_DATABASE_URL (direct) | Pending — user must supply from Neon Console |
| SSL enforcement | Implemented in `database.py` (auto-appends `sslmode=require`) |
| Pool settings | `pool_pre_ping=True`, `pool_size=2`, `max_overflow=3`, `pool_recycle=1800` |

---

## 6. Migration Status

| Item | Status |
|------|--------|
| Alembic `env.py` updated | ✅ Supports `MIGRATION_DATABASE_URL` → `DATABASE_URL` priority |
| Migration script | ✅ `infra/cloudrun/migrate.sh` — checks connectivity, shows revision, runs upgrade head |
| Migrations against Neon | ⏳ Pending — awaiting user credentials and approval |

---

## 7. Synthetic Seed Status

| Item | Status |
|------|--------|
| Seed script idempotent | ✅ Upserts by stable IDs — safe to run multiple times |
| `--reset --confirm-reset` guard | ✅ Requires explicit double-flag to prevent accidents |
| `--verify` flag | ✅ Checks all expected rows without mutations |
| Seeding against Neon | ⏳ Pending — awaiting user approval |

**Synthetic data inventory:**
- Anna Petrova (caregiver) + Maria Petrova (assisted user) — synthetic, no real PII
- Approved caregiver relationship
- 3 active low-risk routines (water plants, drink water, listen to music)
- 1 rejected prohibited routine (medication dose change)
- 1 completed routine (morning tea)
- 1 help-requested caregiver alert

---

## 8. Secret Manager Inventory (Values Not Shown)

| Secret Name | Consumed by | Status |
|-------------|-------------|--------|
| `memorybridge-database-url` | Backend | ⏳ Pending creation by user |
| `memorybridge-migration-database-url` | Migration script | ⏳ Pending creation by user |
| `memorybridge-google-api-key` | Backend | ⏳ Pending creation by user |
| `memorybridge-session-secret` | Web | ⏳ Pending creation by user |
| `memorybridge-caregiver-token` | Web | ⏳ Pending creation by user |
| `memorybridge-assisted-user-token` | Web | ⏳ Pending creation by user |

---

## 9. Service Account and IAM Summary

| Service Account | IAM Roles | Access |
|----------------|-----------|--------|
| `memorybridge-backend-sa` | `secretmanager.secretAccessor` on backend secrets | DATABASE_URL, GOOGLE_API_KEY only |
| `memorybridge-web-sa` | `secretmanager.secretAccessor` on web secrets; `run.invoker` on backend service | SESSION_SECRET, tokens; backend invocation |

Neither service account has Owner, Editor, or project-wide admin roles.

---

## 10. Backend Health Result

| Endpoint | Expected | Actual |
|----------|----------|--------|
| `GET /health` | `{"status":"ok","service":"memorybridge-backend"}` | ⏳ Pending deployment |
| `GET /ready` | `{"status":"ready","service":"memorybridge-backend","provider":"gemini"}` | ⏳ Pending deployment |

---

## 11. Backend Readiness Result

| Check | Description | Status |
|-------|-------------|--------|
| Config loaded | GOOGLE_API_KEY present or AGENT_PROVIDER=fake | ⏳ Pending |
| DATABASE_URL configured | Env var present | ⏳ Pending |
| MCP path locatable | `services/mcp-routines/src/server.py` exists in container | ✅ Verified in Dockerfile |

---

## 12. Public Web URL

⏳ To be populated after deployment:

```
https://memorybridge-web-XXXX-XX.a.run.app
```

---

## 13. Caregiver Smoke-Check Result

⏳ Pending deployment. Will be verified by `smoke-check.sh`:
- Login page accessible
- Caregiver can list routines
- Routine creation returns structured draft

---

## 14. Assisted-User Smoke-Check Result

⏳ Pending deployment. Will be verified by `smoke-check.sh`:
- `/today` API responds 200
- Active routines visible for Maria

---

## 15. Low-Risk Routine Smoke-Check Result

⏳ Pending deployment. Test: submit "Remind Maria to water the plants at 10:00" → verify `safety_decision=allow_for_review`.

---

## 16. Help Alert Smoke-Check Result

⏳ Pending deployment. Test: POST `/api/users/user-assisted-maria/help` → verify `alert_created`.

---

## 17. Prohibited Medication Smoke-Check Result

⏳ Pending deployment. Test: submit "Increase Maria medication dose" → verify `safety_decision=reject_prohibited` in response body.

---

## 18. Secret-Exposure Verification

| Check | Description | Status |
|-------|-------------|--------|
| Web home page body scan | No connection strings or API keys | ✅ Implemented in smoke-check.sh |
| API response body scan | No credentials in alerts response | ✅ Implemented in smoke-check.sh |
| `/ready` endpoint | Redacted — no URL or keys in response | ✅ Implemented in main.py |
| Docker image scan | `.env` excluded by .dockerignore | ✅ Verified |
| `NEXT_PUBLIC_` prefix | No secrets use this prefix | ✅ Verified in codebase |

---

## 19. Rollback Readiness

| Capability | Status |
|-----------|--------|
| Cloud Run revision list | `gcloud run revisions list` — documented in ROLLBACK.md |
| Traffic reroute to previous revision | `gcloud run services update-traffic` — documented |
| Alembic downgrade | Documented with safety caveats |
| Demo data reseed | `./infra/cloudrun/seed.sh` — idempotent |
| Full reset with guard | `./infra/cloudrun/seed.sh --reset --confirm-reset` |
| Secret rotation | Documented in ROLLBACK.md section 4 |
| Incident checklist | Documented in ROLLBACK.md section 5 |

---

## 20. Known Limitations

| ID | Limitation | Severity | Phase |
|----|-----------|---------|-------|
| L-01 | Rate limiter is in-memory (per-process) | Low | Documented from Phase 5; Redis needed for multi-instance |
| L-02 | CSP uses `unsafe-inline` for scripts | Low | Required by Next.js 16; nonce-based deferred |
| L-03 | Demo auth uses static bearer tokens | Low | Acceptable for capstone; real OAuth in future |
| L-04 | E2E Playwright test requires `TEST_DATABASE_URL` | Low | Unblocked by Neon deployment; see Phase 5 L-01 |
| L-05 | Agent Engine not deployed | Info | Documented as optional future work in ARCHITECTURE.md |
| L-06 | `MEMORYBRIDGE_MODEL` default changed | Info | `gemini-2.5-pro` → `gemini-2.5-flash`; both supported until Oct 2026 |
| L-07 | Smoke checks pending deployment approval | Blocker | Results to be filled after user approves and runs deployment |

---

## 21. Final Result

**PASS WITH DOCUMENTED LIMITATIONS**

All Phase 6 preparation work is complete:

- ✅ `.gitignore` updated with required Phase 6 patterns
- ✅ `.env.example` updated with all required variables and model recommendation
- ✅ `MEMORYBRIDGE_MODEL` default aligned: `gemini-2.5-flash` (consistent with `.env.example`)
- ✅ `database.py` updated with Neon-compatible pool settings and SSL enforcement
- ✅ `alembic/env.py` updated to prefer `MIGRATION_DATABASE_URL`
- ✅ `/health` and `/ready` endpoints enhanced (safe, redacted responses)
- ✅ Backend `Dockerfile` (multi-stage, non-root, MCP subprocess included)
- ✅ Web `Dockerfile` (multi-stage, standalone Next.js, non-root, dumb-init)
- ✅ `.dockerignore` files for both services
- ✅ `next.config.ts` updated with `output: "standalone"`
- ✅ `scripts/seed_demo_data.py` — fully idempotent, `--reset --confirm-reset`, `--verify`
- ✅ `infra/cloudrun/deploy-backend.sh`
- ✅ `infra/cloudrun/deploy-web.sh`
- ✅ `infra/cloudrun/migrate.sh`
- ✅ `infra/cloudrun/seed.sh`
- ✅ `infra/cloudrun/smoke-check.sh`
- ✅ `docs/DEPLOYMENT.md`
- ✅ `docs/ROLLBACK.md`
- ✅ `specs/ARCHITECTURE.md` updated with Phase 6 deployment topology
- ✅ `specs/THREAT_MODEL.md` updated with deployment threats
- ✅ `README.md` updated with Phase 6 instructions
- ✅ `specs/PHASE_6_ACCEPTANCE.md` created

**Awaiting user approval and credentials for:**
- Secret Manager secret creation
- IAM service account and role assignment
- Database migration against Neon
- Database seeding against Neon
- Cloud Run deployment (backend and web)
- Smoke check execution

After deployment and smoke check completion, this document will be updated with:
- Public web URL
- Health/ready check results
- Smoke check pass/fail results per item
- Final acceptance status update (expected: PASS)
