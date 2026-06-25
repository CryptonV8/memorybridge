#!/usr/bin/env bash
# =====================================================================
# MemoryBridge — Seed Demo Data
#
# Seeds the synthetic demo personas (Anna Petrova / Maria Petrova)
# into the database. Idempotent by default.
# Requires an explicit --reset --confirm-reset to delete existing rows.
#
# Usage:
#   # Idempotent upsert (safe to run multiple times):
#   DATABASE_URL="postgresql://..." ./infra/cloudrun/seed.sh
#
#   # Reset and re-seed (destructive — requires explicit confirmation):
#   DATABASE_URL="..." ./infra/cloudrun/seed.sh --reset --confirm-reset
#
#   # Verify seed without making changes:
#   DATABASE_URL="..." ./infra/cloudrun/seed.sh --verify
#
# Safety:
#   - Does NOT print DATABASE_URL.
#   - Does NOT delete schema or run DROP TABLE.
#   - --reset ONLY deletes stable demo IDs, not the entire table.
# =====================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MCP_DIR="${REPO_ROOT}/services/mcp-routines"
SEED_SCRIPT="${REPO_ROOT}/scripts/seed_demo_data.py"

RESET_FLAG=""
VERIFY_FLAG=""

# ── Parse arguments ───────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --reset)          RESET_FLAG="--reset"; shift ;;
    --confirm-reset)  RESET_FLAG="${RESET_FLAG} --confirm-reset"; shift ;;
    --verify)         VERIFY_FLAG="--verify"; shift ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

# ── Verify required env ───────────────────────────────────────────────
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set."
  exit 1
fi

echo "=== MemoryBridge Demo Seed ==="
[[ -n "${RESET_FLAG}" ]]  && echo "  Mode: RESET + re-seed"
[[ -n "${VERIFY_FLAG}" ]] && echo "  Mode: VERIFY only"
[[ -z "${RESET_FLAG}${VERIFY_FLAG}" ]] && echo "  Mode: Idempotent upsert"
echo ""

# ── Activate virtual environment ──────────────────────────────────────
VENV="${MCP_DIR}/venv"
if [[ ! -f "${VENV}/bin/python" ]]; then
  echo "ERROR: venv not found at ${VENV}."
  exit 1
fi

# ── Run seed script ───────────────────────────────────────────────────
if [[ -n "${VERIFY_FLAG}" ]]; then
  "${VENV}/bin/python" "${SEED_SCRIPT}" --verify
else
  # shellcheck disable=SC2086
  "${VENV}/bin/python" "${SEED_SCRIPT}" ${RESET_FLAG}
fi

echo ""
echo "✓ Seed step complete."
