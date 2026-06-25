# MemoryBridge — Rollback and Recovery Guide

> **Demo only. Synthetic data. Not a medical device.**

This document covers rollback procedures for Cloud Run revisions, failed migrations, demo-data restoration, secret rotation, and an incident checklist.

---

## 1. Cloud Run revision rollback

### List service revisions

```bash
# Backend
gcloud run revisions list \
  --service memorybridge-backend \
  --region YOUR_REGION \
  --project YOUR_PROJECT \
  --sort-by "~metadata.creationTimestamp" \
  --limit 10

# Web
gcloud run revisions list \
  --service memorybridge-web \
  --region YOUR_REGION \
  --project YOUR_PROJECT \
  --sort-by "~metadata.creationTimestamp" \
  --limit 10
```

### Route traffic to a previous healthy revision

```bash
# Example: route 100% of traffic to the previous stable revision
REVISION="memorybridge-backend-00003-abc"

gcloud run services update-traffic memorybridge-backend \
  --region YOUR_REGION \
  --project YOUR_PROJECT \
  --to-revisions "${REVISION}=100"
```

### Verify health after rollback

```bash
./infra/cloudrun/smoke-check.sh \
  --web-url     "$(gcloud run services describe memorybridge-web --region YOUR_REGION --project YOUR_PROJECT --format 'value(status.url)')" \
  --backend-url "$(gcloud run services describe memorybridge-backend --region YOUR_REGION --project YOUR_PROJECT --format 'value(status.url)')"
```

> **Important:** Do **not** delete the failed revision until investigation is complete. Cloud Run keeps revisions until you explicitly delete them.

### Delete a failed revision (only after investigation)

```bash
gcloud run revisions delete REVISION_NAME \
  --region YOUR_REGION \
  --project YOUR_PROJECT
```

---

## 2. Failed migration response

### Do not continue after a migration failure

If `./infra/cloudrun/migrate.sh` fails:

1. **Stop immediately.** Do not seed or deploy.
2. Inspect the Alembic error output for the failing DDL statement.
3. Determine whether the schema is in a partial state.

### Check current migration revision

```bash
cd services/mcp-routines
MIGRATION_DATABASE_URL="..." ./venv/bin/alembic current
MIGRATION_DATABASE_URL="..." ./venv/bin/alembic history --verbose
```

### Downgrade (only if the migration explicitly supports it)

```bash
# Replace TARGET with the previous revision ID shown in `alembic history`
MIGRATION_DATABASE_URL="..." ./venv/bin/alembic downgrade TARGET
```

> **Warning:** Downgrade is only safe if the migration was designed to be reversible (i.e., it has a `downgrade()` function that undoes the schema change). Do not attempt downgrade on migrations that drop columns or tables — data loss is permanent.

### Neon branch or restore options

Neon supports:
- **Point-in-time restore**: restore the database to a timestamp before the failed migration via the Neon Console.
- **Branch**: create a branch from a known-good restore point and validate the migration there before applying to the main branch.

Refer to the Neon documentation for Console-based restore procedures.

---

## 3. Demo data restoration

### Re-seed without disrupting live users

The seed script is idempotent: running it again upserts only the stable demo rows without deleting anything.

```bash
DATABASE_URL="..." ./infra/cloudrun/seed.sh
```

### Full demo reset (destructive — requires explicit confirmation)

If the demo state is severely corrupted and a clean slate is needed:

```bash
# This deletes existing demo rows by their stable IDs and re-seeds.
# It does NOT drop tables or affect non-demo data.
DATABASE_URL="..." ./infra/cloudrun/seed.sh --reset --confirm-reset
```

> **Safety rule:** Never run `--reset` while a user is actively interacting with the demo. Check Cloud Run request logs to confirm no active session before resetting.

### Verify seed state

```bash
DATABASE_URL="..." ./infra/cloudrun/seed.sh --verify
```

---

## 4. Secret rotation

If a secret is suspected to be compromised:

```bash
export PROJECT="your-project-id"
SECRET_NAME="memorybridge-caregiver-token"

# 1. Add a new version (new value piped from stdin — never echoed)
printf '%s' "NEW_SECRET_VALUE" | \
  gcloud secrets versions add ${SECRET_NAME} \
    --data-file=- --project ${PROJECT}

# 2. Update Cloud Run service to use the new version
gcloud run services update memorybridge-web \
  --region YOUR_REGION \
  --project YOUR_PROJECT \
  --update-secrets "DEMO_CAREGIVER_TOKEN=${SECRET_NAME}:latest"

# 3. Verify the service is healthy
./infra/cloudrun/smoke-check.sh --web-url YOUR_WEB_URL

# 4. Disable the compromised version (after verifying the new one works)
gcloud secrets versions disable VERSION_NUMBER \
  --secret ${SECRET_NAME} \
  --project ${PROJECT}
```

> Disable, do not destroy, the old version until you have confirmed the new secret is working and all services have picked it up.

---

## 5. Incident checklist

Use this checklist for any production incident.

```
INCIDENT: _______________________________
DATE/TIME: ______________________________
REPORTER: _______________________________

[ ] 1. Identify symptom (smoke check output / user report / monitoring alert)
[ ] 2. Capture: service revision, Cloud Logging URL, correlation IDs
[ ] 3. Determine scope: web only / backend only / database / all
[ ] 4. Preserve failed revision — do NOT delete before investigation
[ ] 5. If web is down: roll back to previous revision (see section 1)
[ ] 6. If backend is down: roll back to previous revision (see section 1)
[ ] 7. If migration failed: stop seeding/deployment, assess schema state (see section 2)
[ ] 8. If demo data corrupted: re-seed (idempotent, see section 3)
[ ] 9. If secret leaked: rotate immediately (see section 4)
[10] Run smoke checks after every recovery action
[11] Document root cause and resolution in incident log
[12] Update ROLLBACK.md with any new recovery procedures discovered
```

---

## Known limitations

| Limitation | Risk | Resolution |
|-----------|------|-----------|
| Rate limiter is in-memory | Low — per-process only | Replace with Redis-backed store for multi-instance deployments |
| Demo tokens in Secret Manager are static | Low | Rotate periodically or implement short-lived token issuance |
| CSP uses `unsafe-inline` for scripts | Low | Required by Next.js 16; replace with nonce-based CSP in future |
| No automatic database backup schedule | Low | Neon provides PITR; configure alerts for database size growth |
