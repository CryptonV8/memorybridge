# Environment and Secrets Audit Report

This document outlines the environment variables, configuration parameters, and secret boundaries across the MemoryBridge system.

## 1. Audit Results

### 1. Variables Found
- `GOOGLE_CLOUD_PROJECT` (Deployment)
- `GOOGLE_CLOUD_REGION` (Deployment)
- `DATABASE_URL` (Backend MCP runtime)
- `MIGRATION_DATABASE_URL` (Migration script only)
- `GOOGLE_API_KEY` (Backend Gemini integration)
- `MEMORYBRIDGE_MODEL` (Backend Gemini configuration)
- `AGENT_PROVIDER` (Backend Gemini/Fake switch)
- `SESSION_SECRET` (Web iron-session encryption)
- `DEMO_CAREGIVER_TOKEN` (Shared boundary authentication)
- `DEMO_ASSISTED_USER_TOKEN` (Shared boundary authentication)
- `AGENT_API_BASE_URL` (Web internal routing)
- `ALLOWED_ORIGINS` (Backend CORS)
- `ENVIRONMENT` (Backend mode)
- `LOG_LEVEL` (Backend logging)
- `TEST_DATABASE_URL` (Local E2E tests)
- `OTEL_EXPORTER_OTLP_ENDPOINT` (Backend telemetry)
- `OTEL_SERVICE_NAME` (Backend telemetry)

### 2. Missing Variables
- None.

### 3. Duplicate or Obsolete Variables
- No occurrences of `GEMINI_API_KEY` exist. The system correctly standardizes on `GOOGLE_API_KEY` as expected by `google-genai` and `google-adk`.
- No `NEXT_PUBLIC_` prefixed secret variables found.

### 4. `.env` and GitIgnore Status
- ✅ `.env` is listed in `.gitignore`.
- ✅ `.env.local`, `apps/web/.env.local`, and other environment files are excluded.
- ✅ The root `.env` exists locally and contains keys but is strictly excluded from git.
- ✅ Tested using `git check-ignore -v .env`.

### 5. `.env.example` Status
- ✅ Only contains empty placeholders or safe defaults (e.g. `MEMORYBRIDGE_MODEL=gemini-2.5-flash`).
- ✅ No real secrets present.

### 6. Gemini Configuration Result
- `config.py` correctly uses `pydantic-settings` to load `GOOGLE_API_KEY`.
- `main.py` validates its presence strictly when `AGENT_PROVIDER=gemini`.
- `fake` mode ignores the key safely.

### 7. Caregiver Token Validation
- ✅ Modified `dependencies.py` to use `DEMO_CAREGIVER_TOKEN` dynamically from environment instead of hardcoded dictionary.
- ✅ `security.test.ts` changed to read from test environment rather than a hardcoded sentinel.

### 8. Assisted-User Token Validation
- ✅ Modified `dependencies.py` to use `DEMO_ASSISTED_USER_TOKEN` dynamically from environment.
- ✅ `today.test.tsx` modified to use environment variables for scanning assets.

### 9. Role-Separation Result
- ✅ A specific unit test `test_role_separation` was added to `test_api.py` validating that the caregiver token assumes the `caregiver` role, and the assisted-user token assumes the `assisted_user` role exactly.
- ✅ They cannot be interchanged because `dependencies.py` looks up the exact string match against the configured settings.

### 10. Cloud Run Secret Ownership Corrections
- ✅ Modified `infra/cloudrun/deploy-backend.sh` to inject `DEMO_CAREGIVER_TOKEN` and `DEMO_ASSISTED_USER_TOKEN` into the backend.
- ✅ Modified `docs/DEPLOYMENT.md` to grant the `memorybridge-backend-sa` service account access to those tokens in Secret Manager.
- ✅ Web service access boundary unchanged and correct. Migration database URL boundary unchanged and correct.
- ✅ Updated `docs/DEPLOYMENT.md` examples to use `read -s` instead of `printf` with literal secrets to prevent bash history leaks.

### 11. Files Changed
- `services/agent-api/src/memorybridge_agent/config.py`
- `services/agent-api/src/memorybridge_agent/dependencies.py`
- `services/agent-api/tests/test_api.py`
- `apps/web/tests/security.test.ts`
- `apps/web/tests/today.test.tsx`
- `infra/cloudrun/deploy-backend.sh`
- `docs/DEPLOYMENT.md`
- `docs/ENVIRONMENT_AND_SECRETS.md` (this file)

### 12. Blockers Before Deployment
- **None.** The configuration is clean, secure, separated, and correctly documented.

---

## 2. Variable Inventory

| Variable | Secret? | Service | Local Source | Cloud Run Source | Secret Manager Name | Required (Fake) | Required (Gemini) | Browser Exp. |
|----------|---------|---------|--------------|------------------|---------------------|-----------------|-------------------|--------------|
| `GOOGLE_CLOUD_PROJECT` | No | CLI | shell export | - | - | Yes | Yes | None |
| `GOOGLE_CLOUD_REGION` | No | CLI | shell export | - | - | Yes | Yes | None |
| `DATABASE_URL` | Yes | Backend | `.env` | Secret Manager | `memorybridge-database-url` | Yes | Yes | None |
| `MIGRATION_DATABASE_URL` | Yes | Migrations | `.env` | Secret Manager | `memorybridge-migration-database-url` | Yes | Yes | None |
| `GOOGLE_API_KEY` | Yes | Backend | `.env` | Secret Manager | `memorybridge-google-api-key` | No | Yes | None |
| `MEMORYBRIDGE_MODEL` | No | Backend | `.env` | Env Var | - | No | Yes | None |
| `AGENT_PROVIDER` | No | Backend | `.env` | Env Var | - | Yes | Yes | None |
| `SESSION_SECRET` | Yes | Web | `.env` / `.env.local` | Secret Manager | `memorybridge-session-secret` | Yes | Yes | None |
| `DEMO_CAREGIVER_TOKEN` | Yes | Web, Backend | `.env` / `.env.local` | Secret Manager | `memorybridge-caregiver-token` | Yes | Yes | None |
| `DEMO_ASSISTED_USER_TOKEN` | Yes | Web, Backend | `.env` / `.env.local` | Secret Manager | `memorybridge-assisted-user-token` | Yes | Yes | None |
| `AGENT_API_BASE_URL` | No | Web | `.env` / `.env.local` | Env Var | - | Yes | Yes | None |
| `ALLOWED_ORIGINS` | No | Backend | `.env` | Env Var | - | Yes | Yes | None |
| `ENVIRONMENT` | No | Web, Backend | `.env` / `.env.local` | Env Var | - | Yes | Yes | None |
| `LOG_LEVEL` | No | Backend | `.env` | Env Var | - | Yes | Yes | None |

## 3. Local Development Root `.env` Loading
- **Backend (FastAPI):** `pydantic-settings` directly reads `.env` from the execution directory (the monorepo root in development).
- **Web (Next.js):** By default Next.js looks for `.env` or `.env.local` in `apps/web/`. To maintain a single source of truth without duplicating secrets, developers should symlink the root file:
  ```bash
  cd apps/web
  ln -s ../../.env .env.local
  ```
  This symlink is correctly ignored by git via `.gitignore`.
