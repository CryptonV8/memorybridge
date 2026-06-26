#!/usr/bin/env bash
# =====================================================================
# MemoryBridge — Deploy Backend (Cloud Run)
#
# Builds and deploys the memorybridge-backend Cloud Run service.
# The backend is deployed as a PRIVATE service; only the web service
# account and explicitly authorized developer identities may invoke it.
#
# Usage:
#   ./infra/cloudrun/deploy-backend.sh \
#     --project  my-gcp-project \
#     --region   europe-west1 \
#     --image-tag v1.0.0
#
# Prerequisites:
#   - gcloud authenticated and configured
#   - Artifact Registry repository created (see docs/DEPLOYMENT.md)
#   - Secret Manager secrets created (see docs/DEPLOYMENT.md)
#   - Service account memorybridge-backend-sa exists
# =====================================================================
set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────
PROJECT=""
REGION=""
IMAGE_TAG="latest"
SERVICE_NAME="memorybridge-backend"
SA_NAME="memorybridge-backend-sa"
REPO_NAME="memorybridge"

# ── Parse arguments ───────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)  PROJECT="$2";  shift 2 ;;
    --region)   REGION="$2";   shift 2 ;;
    --image-tag) IMAGE_TAG="$2"; shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

if [[ -z "$PROJECT" || -z "$REGION" ]]; then
  echo "ERROR: --project and --region are required."
  echo "Usage: $0 --project PROJECT --region REGION [--image-tag TAG]"
  exit 1
fi

SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
ARTIFACT_REGISTRY="${REGION}-docker.pkg.dev/${PROJECT}/${REPO_NAME}"
IMAGE="${ARTIFACT_REGISTRY}/backend:${IMAGE_TAG}"

echo "=== MemoryBridge Backend Deployment ==="
echo "  Project:  ${PROJECT}"
echo "  Region:   ${REGION}"
echo "  Service:  ${SERVICE_NAME}"
echo "  Image:    ${IMAGE}"
echo ""

# ── Build and push the image ──────────────────────────────────────────
echo "[1/4] Building and pushing backend image using Google Cloud Build..."
# Build context is the monorepo root so Cloud Build can COPY cross-service files
# We temporarily copy the Dockerfile to the root to use gcloud builds submit without docker
cp services/agent-api/Dockerfile Dockerfile
# Ensure we cleanup on exit or error
trap 'rm -f Dockerfile' EXIT ERR INT TERM

gcloud builds submit \
  --project "${PROJECT}" \
  --tag "${IMAGE}" \
  .

rm -f Dockerfile
# Clear trap
trap - EXIT ERR INT TERM

# ── Deploy to Cloud Run ───────────────────────────────────────────────
echo "[3/4] Deploying to Cloud Run (private — no unauthenticated access)..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT}" \
  --service-account "${SA_EMAIL}" \
  --no-allow-unauthenticated \
  --concurrency 10 \
  --min-instances 0 \
  --max-instances 3 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60s \
  --port 8080 \
  --set-env-vars "ENVIRONMENT=production,LOG_LEVEL=INFO,AGENT_PROVIDER=gemini,MEMORYBRIDGE_MODEL=gemini-2.5-flash" \
  --set-secrets "\
DATABASE_URL=memorybridge-database-url:latest,\
GOOGLE_API_KEY=memorybridge-google-api-key:latest,\
DEMO_CAREGIVER_TOKEN=memorybridge-caregiver-token:latest,\
DEMO_ASSISTED_USER_TOKEN=memorybridge-assisted-user-token:latest" \
  --platform managed \
  --quiet

# ── Retrieve and print the backend URL ────────────────────────────────
echo "[4/4] Retrieving backend service URL..."
BACKEND_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT}" \
  --format "value(status.url)")

echo ""
echo "✓ Backend deployed successfully."
echo "  URL (private): ${BACKEND_URL}"
echo ""
echo "  Next step: run deploy-web.sh with --backend-url ${BACKEND_URL}"
