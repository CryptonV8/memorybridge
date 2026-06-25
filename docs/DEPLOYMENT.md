# MemoryBridge — Deployment Guide

> **Demo only. Synthetic data. Not a medical device.**

This guide covers deploying MemoryBridge to Google Cloud Run using Neon PostgreSQL as the managed database. Follow each section in order.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Required credentials and values](#2-required-credentials-and-values)
3. [Neon PostgreSQL configuration](#3-neon-postgresql-configuration)
4. [Google Cloud preparation](#4-google-cloud-preparation)
5. [Secret Manager setup](#5-secret-manager-setup)
6. [Artifact Registry](#6-artifact-registry)
7. [Database migration](#7-database-migration)
8. [Demo data seeding](#8-demo-data-seeding)
9. [Backend deployment](#9-backend-deployment)
10. [Web deployment](#10-web-deployment)
11. [CORS and allowed origins](#11-cors-and-allowed-origins)
12. [Smoke verification](#12-smoke-verification)
13. [Public URL retrieval](#13-public-url-retrieval)
14. [Cleanup guidance](#14-cleanup-guidance)

---

## 1. Prerequisites

### Local tools

| Tool | Minimum version | Purpose |
|------|----------------|---------|
| `gcloud` CLI | 2024.x | Cloud Run, Secret Manager, IAM |
| `docker` | 24.x | Build container images |
| `python` | 3.11 | Migrations, seed script |
| `node` | 20.x | Local web build (optional) |
| `curl` | any | Smoke checks |

Verify your `gcloud` installation:

```bash
gcloud --version
gcloud auth list           # confirm authenticated identity
gcloud config get-value project
```

### Authenticate with Docker to Artifact Registry

```bash
gcloud auth configure-docker REGION-docker.pkg.dev
```

---

## 2. Required credentials and values

You must supply the following before deploying. Do **not** paste values into chat or commit them.

Place them in a local `.env` file (gitignored):

| Variable | Where to get it | Secret? |
|----------|----------------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP Console → Project ID | No |
| `GOOGLE_CLOUD_REGION` | Choose a region (e.g. `europe-west1`) | No |
| `DATABASE_URL` | Neon Console → Connection String → Pooled | **YES** |
| `MIGRATION_DATABASE_URL` | Neon Console → Connection String → Direct | **YES** |
| `GOOGLE_API_KEY` | Google AI Studio → API key | **YES** |
| `SESSION_SECRET` | Generate: `openssl rand -hex 32` | **YES** |
| `DEMO_CAREGIVER_TOKEN` | Choose a strong random string | **YES** |
| `DEMO_ASSISTED_USER_TOKEN` | Choose a strong random string | **YES** |
| `MEMORYBRIDGE_MODEL` | `gemini-2.5-flash` (recommended) | No |

---

## 3. Neon PostgreSQL configuration

MemoryBridge uses the existing **MemoryBridge** Neon project. You do **not** need to create a new project.

### Connection strings

Neon provides two types of connection strings in the Console:

| Type | Variable | Use for |
|------|----------|---------|
| **Pooled** (PgBouncer) | `DATABASE_URL` | Runtime (MCP server, FastAPI) |
| **Direct / Unpooled** | `MIGRATION_DATABASE_URL` | Alembic migrations only |

Both must include `?sslmode=require`. Neon adds this by default in the Console.

> **Note:** `database.py` enforces SSL automatically if the URL does not already include `sslmode`.

### Verify connectivity

```bash
# Install psycopg2 if needed: pip install psycopg2-binary
python -c "
import os
from sqlalchemy import create_engine, text
url = os.environ['MIGRATION_DATABASE_URL']
engine = create_engine(url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT version()'))
    print(result.scalar())
"
```

---

## 4. Google Cloud preparation

Run these commands once per project. Replace placeholders with your values.

```bash
export PROJECT="your-project-id"
export REGION="europe-west1"

# Select project
gcloud config set project ${PROJECT}

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  --project ${PROJECT}

# Create dedicated service accounts
gcloud iam service-accounts create memorybridge-backend-sa \
  --display-name "MemoryBridge Backend" \
  --project ${PROJECT}

gcloud iam service-accounts create memorybridge-web-sa \
  --display-name "MemoryBridge Web" \
  --project ${PROJECT}

# Grant backend SA the Cloud Run Invoker role on itself (for self-checks if needed)
# The web SA needs run.invoker to call the private backend
gcloud projects add-iam-policy-binding ${PROJECT} \
  --member "serviceAccount:memorybridge-web-sa@${PROJECT}.iam.gserviceaccount.com" \
  --role "roles/run.invoker"

# Allow web service to invoke the backend service specifically
# (Done after backend is deployed — see step 9)
```

> **Principle of least privilege:** Neither service account has Owner or Editor. The web SA gets only `run.invoker`. The backend SA gets only `secretmanager.secretAccessor` on its own secrets.

---

## 5. Secret Manager setup

Create each secret by piping the value from stdin. **Never** echo secrets in shell history.

```bash
export PROJECT="your-project-id"

# Example for one secret: read securely without echoing to shell history
echo -n "Enter backend DATABASE_URL: " && read -s SECRET_VAL && echo "" && \
  printf '%s' "$SECRET_VAL" | gcloud secrets create memorybridge-database-url --data-file=- --project ${PROJECT}

echo -n "Enter MIGRATION_DATABASE_URL: " && read -s SECRET_VAL && echo "" && \
  printf '%s' "$SECRET_VAL" | gcloud secrets create memorybridge-migration-database-url --data-file=- --project ${PROJECT}

echo -n "Enter GOOGLE_API_KEY: " && read -s SECRET_VAL && echo "" && \
  printf '%s' "$SECRET_VAL" | gcloud secrets create memorybridge-google-api-key --data-file=- --project ${PROJECT}

echo -n "Enter SESSION_SECRET: " && read -s SECRET_VAL && echo "" && \
  printf '%s' "$SECRET_VAL" | gcloud secrets create memorybridge-session-secret --data-file=- --project ${PROJECT}

echo -n "Enter DEMO_CAREGIVER_TOKEN: " && read -s SECRET_VAL && echo "" && \
  printf '%s' "$SECRET_VAL" | gcloud secrets create memorybridge-caregiver-token --data-file=- --project ${PROJECT}

echo -n "Enter DEMO_ASSISTED_USER_TOKEN: " && read -s SECRET_VAL && echo "" && \
  printf '%s' "$SECRET_VAL" | gcloud secrets create memorybridge-assisted-user-token --data-file=- --project ${PROJECT}

# Grant backend SA access to its secrets
BACKEND_SA="memorybridge-backend-sa@${PROJECT}.iam.gserviceaccount.com"
for SECRET in memorybridge-database-url memorybridge-google-api-key memorybridge-caregiver-token memorybridge-assisted-user-token; do
  gcloud secrets add-iam-policy-binding ${SECRET} \
    --member "serviceAccount:${BACKEND_SA}" \
    --role "roles/secretmanager.secretAccessor" \
    --project ${PROJECT}
done

# Grant web SA access to web secrets only
WEB_SA="memorybridge-web-sa@${PROJECT}.iam.gserviceaccount.com"
for SECRET in memorybridge-session-secret memorybridge-caregiver-token memorybridge-assisted-user-token; do
  gcloud secrets add-iam-policy-binding ${SECRET} \
    --member "serviceAccount:${WEB_SA}" \
    --role "roles/secretmanager.secretAccessor" \
    --project ${PROJECT}
done
```

### Secret inventory

| Secret name | Consumed by | Contains |
|-------------|-------------|---------|
| `memorybridge-database-url` | Backend | Neon pooled connection string |
| `memorybridge-migration-database-url` | Migration script only | Neon direct connection string |
| `memorybridge-google-api-key` | Backend | Google AI Studio API key |
| `memorybridge-session-secret` | Web | iron-session encryption secret |
| `memorybridge-caregiver-token` | Web | Demo caregiver bearer token |
| `memorybridge-assisted-user-token` | Web | Demo assisted-user bearer token |

---

## 6. Artifact Registry

```bash
export PROJECT="your-project-id"
export REGION="europe-west1"

# Create repository
gcloud artifacts repositories create memorybridge \
  --repository-format docker \
  --location ${REGION} \
  --description "MemoryBridge container images" \
  --project ${PROJECT}

# Authenticate Docker
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

---

## 7. Database migration

Run migrations **before** deploying services. Use the direct/unpooled connection string.

```bash
# Set the migration URL (do not echo it)
export MIGRATION_DATABASE_URL="$(gcloud secrets versions access latest \
  --secret memorybridge-migration-database-url --project YOUR_PROJECT)"

# Run migrations
./infra/cloudrun/migrate.sh
```

If migration fails, **stop**. Do not seed or deploy until the migration issue is resolved. See [docs/ROLLBACK.md](ROLLBACK.md) for recovery steps.

---

## 8. Demo data seeding

After successful migrations, seed synthetic demo data:

```bash
export DATABASE_URL="$(gcloud secrets versions access latest \
  --secret memorybridge-database-url --project YOUR_PROJECT)"

# Idempotent upsert (safe to run multiple times)
./infra/cloudrun/seed.sh

# Verify seed
./infra/cloudrun/seed.sh --verify
```

To restore demo data after it has been modified during a live demo:

```bash
./infra/cloudrun/seed.sh
```

For a full reset (deletes existing demo rows and re-seeds):

```bash
./infra/cloudrun/seed.sh --reset --confirm-reset
```

> **Safety:** Reset only deletes the stable demo IDs. It does not drop tables or affect any non-demo data.

---

## 9. Backend deployment

```bash
./infra/cloudrun/deploy-backend.sh \
  --project  YOUR_PROJECT \
  --region   YOUR_REGION \
  --image-tag v1.0.0
```

After deployment, grant the web service account permission to invoke the backend:

```bash
BACKEND_URL=$(gcloud run services describe memorybridge-backend \
  --region YOUR_REGION --project YOUR_PROJECT \
  --format "value(status.url)")

gcloud run services add-iam-policy-binding memorybridge-backend \
  --region YOUR_REGION \
  --project YOUR_PROJECT \
  --member "serviceAccount:memorybridge-web-sa@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role "roles/run.invoker"
```

---

## 10. Web deployment

```bash
./infra/cloudrun/deploy-web.sh \
  --project      YOUR_PROJECT \
  --region       YOUR_REGION \
  --backend-url  "${BACKEND_URL}" \
  --image-tag    v1.0.0
```

---

## 11. CORS and allowed origins

After the web service is deployed, retrieve its URL and update the backend if you need to restrict CORS:

```bash
WEB_URL=$(gcloud run services describe memorybridge-web \
  --region YOUR_REGION --project YOUR_PROJECT \
  --format "value(status.url)")

# Update backend ALLOWED_ORIGINS env var
gcloud run services update memorybridge-backend \
  --region YOUR_REGION \
  --project YOUR_PROJECT \
  --update-env-vars "ALLOWED_ORIGINS=${WEB_URL}"
```

### CORS policy

| Context | Policy |
|---------|--------|
| Browser → Backend | **Not applicable** — browsers never call the backend directly |
| Web server → Backend | Server-to-server via Cloud Run IAM; no CORS headers needed |
| Backend CORS header | Restricted to `ALLOWED_ORIGINS` (the web Cloud Run URL only) |
| Wildcard `*` | **Never used** for credentialed requests |

---

## 12. Smoke verification

```bash
./infra/cloudrun/smoke-check.sh \
  --web-url "${WEB_URL}" \
  --backend-url "${BACKEND_URL}" \
  --caregiver-token "$(gcloud secrets versions access latest \
      --secret memorybridge-caregiver-token --project YOUR_PROJECT)" \
  --assisted-user-token "$(gcloud secrets versions access latest \
      --secret memorybridge-assisted-user-token --project YOUR_PROJECT)"
```

Expected result: all 10 checks PASS (or SKIP for optional checks).

---

## 13. Public URL retrieval

```bash
gcloud run services describe memorybridge-web \
  --region YOUR_REGION \
  --project YOUR_PROJECT \
  --format "value(status.url)"
```

---

## 14. Cleanup guidance

To stop serving traffic without destroying data:

```bash
# Scale to zero (no cost when not serving)
gcloud run services update memorybridge-web \
  --min-instances 0 --region YOUR_REGION --project YOUR_PROJECT

gcloud run services update memorybridge-backend \
  --min-instances 0 --region YOUR_REGION --project YOUR_PROJECT
```

To delete Cloud Run services (reversible — does not affect database):

```bash
gcloud run services delete memorybridge-web    --region YOUR_REGION --project YOUR_PROJECT
gcloud run services delete memorybridge-backend --region YOUR_REGION --project YOUR_PROJECT
```

> **Note:** Deleting services does **not** delete secrets or the Neon database. These must be removed separately if desired.
