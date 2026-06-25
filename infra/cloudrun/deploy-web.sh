#!/usr/bin/env bash
# =====================================================================
# MemoryBridge — Deploy Web (Cloud Run)
#
# Builds and deploys the memorybridge-web Cloud Run service.
# The web service is PUBLIC (allows unauthenticated access from browsers).
# It calls the PRIVATE backend only from server-side code.
#
# Usage:
#   ./infra/cloudrun/deploy-web.sh \
#     --project      my-gcp-project \
#     --region       europe-west1 \
#     --backend-url  https://memorybridge-backend-xxxx-ew.a.run.app \
#     --image-tag    v1.0.0
#
# Prerequisites:
#   - Backend already deployed (run deploy-backend.sh first)
#   - gcloud authenticated and configured
#   - Artifact Registry repository created
#   - Secret Manager secrets created (session-secret, caregiver-token, assisted-user-token)
#   - Service account memorybridge-web-sa exists
# =====================================================================
set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────
PROJECT=""
REGION=""
BACKEND_URL=""
IMAGE_TAG="latest"
SERVICE_NAME="memorybridge-web"
SA_NAME="memorybridge-web-sa"
REPO_NAME="memorybridge"

# ── Parse arguments ───────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)     PROJECT="$2";     shift 2 ;;
    --region)      REGION="$2";      shift 2 ;;
    --backend-url) BACKEND_URL="$2"; shift 2 ;;
    --image-tag)   IMAGE_TAG="$2";   shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

if [[ -z "$PROJECT" || -z "$REGION" || -z "$BACKEND_URL" ]]; then
  echo "ERROR: --project, --region, and --backend-url are required."
  echo "Usage: $0 --project PROJECT --region REGION --backend-url URL [--image-tag TAG]"
  exit 1
fi

SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
ARTIFACT_REGISTRY="${REGION}-docker.pkg.dev/${PROJECT}/${REPO_NAME}"
IMAGE="${ARTIFACT_REGISTRY}/web:${IMAGE_TAG}"

echo "=== MemoryBridge Web Deployment ==="
echo "  Project:     ${PROJECT}"
echo "  Region:      ${REGION}"
echo "  Service:     ${SERVICE_NAME}"
echo "  Backend URL: ${BACKEND_URL}"
echo "  Image:       ${IMAGE}"
echo ""

# ── Build and push the image ──────────────────────────────────────────
echo "[1/4] Building web image from monorepo root..."
# Build context is the monorepo root; web Dockerfile uses COPY apps/web/
docker build \
  --file apps/web/Dockerfile \
  --tag "${IMAGE}" \
  --label "git-commit=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)" \
  .

echo "[2/4] Pushing image to Artifact Registry..."
docker push "${IMAGE}"

# ── Deploy to Cloud Run ───────────────────────────────────────────────
echo "[3/4] Deploying web service (public — allows unauthenticated browser access)..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT}" \
  --service-account "${SA_EMAIL}" \
  --allow-unauthenticated \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 5 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 30s \
  --port 3000 \
  --set-env-vars "ENVIRONMENT=production,NODE_ENV=production,AGENT_API_BASE_URL=${BACKEND_URL}" \
  --set-secrets "\
SESSION_SECRET=memorybridge-session-secret:latest,\
DEMO_CAREGIVER_TOKEN=memorybridge-caregiver-token:latest,\
DEMO_ASSISTED_USER_TOKEN=memorybridge-assisted-user-token:latest" \
  --platform managed \
  --quiet

# ── Retrieve and print the public URL ─────────────────────────────────
echo "[4/4] Retrieving web service URL..."
WEB_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT}" \
  --format "value(status.url)")

echo ""
echo "✓ Web service deployed successfully."
echo "  Public URL: ${WEB_URL}"
echo ""
echo "  Next steps:"
echo "    1. Update backend ALLOWED_ORIGINS with: ${WEB_URL}"
echo "    2. Run smoke checks: ./infra/cloudrun/smoke-check.sh --web-url ${WEB_URL} --backend-url ${BACKEND_URL}"
