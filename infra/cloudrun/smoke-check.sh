#!/usr/bin/env bash
# =====================================================================
# MemoryBridge — Smoke Checks
#
# Performs the 10 essential post-deployment smoke checks.
# Does NOT rerun the full Phase 1–5 test suite.
#
# Usage:
#   ./infra/cloudrun/smoke-check.sh \
#     --web-url     https://memorybridge-web-xxxx.a.run.app \
#     --backend-url https://memorybridge-backend-xxxx.a.run.app \
#     --caregiver-token YOUR_DEMO_CAREGIVER_TOKEN \
#     --assisted-user-token YOUR_DEMO_ASSISTED_USER_TOKEN
#
# The caregiver-token and assisted-user-token flags are optional.
# If not provided, the script only checks publicly accessible endpoints.
# NEVER paste real credentials into this script or its output.
# =====================================================================
set -euo pipefail

WEB_URL=""
BACKEND_URL=""
CAREGIVER_TOKEN=""
ASSISTED_TOKEN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --web-url)              WEB_URL="$2";         shift 2 ;;
    --backend-url)          BACKEND_URL="$2";     shift 2 ;;
    --caregiver-token)      CAREGIVER_TOKEN="$2"; shift 2 ;;
    --assisted-user-token)  ASSISTED_TOKEN="$2";  shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

if [[ -z "$WEB_URL" ]]; then
  echo "ERROR: --web-url is required."
  exit 1
fi

PASS=0
FAIL=0
SKIP=0

pass() { echo "  ✓ PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  ✗ FAIL: $1"; FAIL=$((FAIL+1)); }
skip() { echo "  - SKIP: $1"; SKIP=$((SKIP+1)); }

echo "=== MemoryBridge Smoke Checks ==="
echo "  Web URL:     ${WEB_URL}"
echo "  Backend URL: ${BACKEND_URL:-not provided}"
echo ""

# ── Check 1: Backend /health ──────────────────────────────────────────
if [[ -n "${BACKEND_URL}" ]]; then
  STATUS=$(curl -sf -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${CAREGIVER_TOKEN}" \
    "${BACKEND_URL}/health" 2>/dev/null || echo "000")
  if [[ "${STATUS}" == "200" ]]; then
    pass "Backend /health responds 200"
  else
    fail "Backend /health returned ${STATUS}"
  fi
else
  skip "Backend /health (--backend-url not provided)"
fi

# ── Check 2: Backend /ready ───────────────────────────────────────────
if [[ -n "${BACKEND_URL}" && -n "${CAREGIVER_TOKEN}" ]]; then
  STATUS=$(curl -sf -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${CAREGIVER_TOKEN}" \
    "${BACKEND_URL}/ready" 2>/dev/null || echo "000")
  if [[ "${STATUS}" == "200" ]]; then
    pass "Backend /ready responds 200"
  else
    fail "Backend /ready returned ${STATUS} (check SECRET_MANAGER and DATABASE_URL)"
  fi
else
  skip "Backend /ready (--backend-url or --caregiver-token not provided)"
fi

# ── Check 3: Web service loads over HTTPS ─────────────────────────────
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "${WEB_URL}/" 2>/dev/null || echo "000")
if [[ "${STATUS}" == "200" || "${STATUS}" == "302" || "${STATUS}" == "307" ]]; then
  pass "Web service loads (HTTP ${STATUS})"
else
  fail "Web service returned HTTP ${STATUS}"
fi

# ── Check 4: No secret visible in web home page ───────────────────────
BODY=$(curl -sf "${WEB_URL}/" 2>/dev/null || echo "")
if echo "${BODY}" | grep -qiE "(demo-token|SESSION_SECRET|GOOGLE_API_KEY|neon\.tech|postgres://|postgresql://)"; then
  fail "Web home page contains what looks like a secret or connection string"
else
  pass "No visible secret in web home page response"
fi

# ── Check 5: Caregiver login page accessible ──────────────────────────
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "${WEB_URL}/login" 2>/dev/null || echo "000")
if [[ "${STATUS}" == "200" || "${STATUS}" == "302" || "${STATUS}" == "307" ]]; then
  pass "Caregiver login page accessible (${STATUS})"
else
  fail "Caregiver login page returned ${STATUS}"
fi

# ── Checks 6–10: Require token — skip if not provided ────────────────
if [[ -z "${CAREGIVER_TOKEN}" || -z "${BACKEND_URL}" ]]; then
  skip "Checks 6-10 skipped (--caregiver-token and --backend-url required for API checks)"
  skip "Routine creation smoke check"
  skip "Maria today view smoke check"
  skip "Help alert smoke check"
  skip "Prohibited medication smoke check"
else
  # ── Check 6: Caregiver can list routines ─────────────────────────────
  STATUS=$(curl -sf -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${CAREGIVER_TOKEN}" \
    "${BACKEND_URL}/api/caregivers/me/routines" 2>/dev/null || echo "000")
  if [[ "${STATUS}" == "200" ]]; then
    pass "Caregiver can list routines"
  else
    fail "Caregiver routines returned ${STATUS}"
  fi

  # ── Check 7: Maria's today view ───────────────────────────────────────
  if [[ -n "${ASSISTED_TOKEN}" ]]; then
    STATUS=$(curl -sf -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer ${ASSISTED_TOKEN}" \
      "${BACKEND_URL}/api/users/user-assisted-maria/today" 2>/dev/null || echo "000")
    if [[ "${STATUS}" == "200" ]]; then
      pass "Maria's today routines endpoint responds 200"
    else
      fail "Maria today returned ${STATUS}"
    fi
  else
    skip "Maria today view (--assisted-user-token not provided)"
  fi

  # ── Check 8: Help me creates a caregiver alert ─────────────────────
  if [[ -n "${ASSISTED_TOKEN}" ]]; then
    STATUS=$(curl -sf -o /dev/null -w "%{http_code}" \
      -X POST \
      -H "Authorization: Bearer ${ASSISTED_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"routine_id":"routine-demo-001","routine_title":"Water the plants"}' \
      "${BACKEND_URL}/api/users/user-assisted-maria/help" 2>/dev/null || echo "000")
    if [[ "${STATUS}" == "200" ]]; then
      pass "Help me creates caregiver alert (200)"
    else
      fail "Help me returned ${STATUS}"
    fi
  else
    skip "Help alert check (--assisted-user-token not provided)"
  fi

  # ── Check 9: Prohibited medication request is rejected ───────────────
  BODY=$(curl -sf \
    -X POST \
    -H "Authorization: Bearer ${CAREGIVER_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"text":"Increase Maria medication dose","assisted_user_id":"user-assisted-maria"}' \
    "${BACKEND_URL}/api/routines/interpret" 2>/dev/null || echo "")
  if echo "${BODY}" | grep -q "reject_prohibited"; then
    pass "Medication dose change request returned reject_prohibited"
  else
    fail "Medication request was not rejected as prohibited: ${BODY:0:200}"
  fi

  # ── Check 10: No secret in API response body ─────────────────────────
  ALERTS=$(curl -sf \
    -H "Authorization: Bearer ${CAREGIVER_TOKEN}" \
    "${BACKEND_URL}/api/caregivers/me/alerts" 2>/dev/null || echo "")
  if echo "${ALERTS}" | grep -qiE "(api_key|secret|password|neon\.tech|postgres://)"; then
    fail "API response body contains what looks like a secret"
  else
    pass "No visible secret in alerts API response"
  fi
fi

# ── Summary ───────────────────────────────────────────────────────────
echo ""
echo "=== Results ==="
echo "  PASS: ${PASS}"
echo "  FAIL: ${FAIL}"
echo "  SKIP: ${SKIP}"
echo ""

if [[ "${FAIL}" -gt 0 ]]; then
  echo "✗ Some smoke checks FAILED. Review the output above."
  exit 1
else
  echo "✓ All executed smoke checks PASSED."
fi
