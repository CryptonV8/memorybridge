#!/usr/bin/env bash
# =====================================================================
# MemoryBridge — Run Database Migrations (Alembic)
#
# Runs Alembic migrations against the Neon PostgreSQL database.
# Uses MIGRATION_DATABASE_URL (unpooled) when available;
# falls back to DATABASE_URL.
#
# Usage:
#   # Run from repository root with DATABASE_URL / MIGRATION_DATABASE_URL in env
#   source .env   # or set env vars manually — do not paste credentials in shell history
#   ./infra/cloudrun/migrate.sh
#
#   # Or pass via environment directly:
#   MIGRATION_DATABASE_URL="postgresql://..." ./infra/cloudrun/migrate.sh
#
# Safety:
#   - Does NOT print connection strings.
#   - Does NOT run destructive DDL automatically.
#   - Checks connectivity before running migrations.
#   - Prints the current head revision after completion.
# =====================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MCP_DIR="${REPO_ROOT}/services/mcp-routines"

# ── Verify required env ───────────────────────────────────────────────
DB_URL="${MIGRATION_DATABASE_URL:-${DATABASE_URL:-}}"
if [[ -z "${DB_URL}" ]]; then
  echo "ERROR: Neither MIGRATION_DATABASE_URL nor DATABASE_URL is set."
  echo "Set one of these before running migrations."
  exit 1
fi

echo "=== MemoryBridge Database Migration ==="
echo "  Using MIGRATION_DATABASE_URL: ${MIGRATION_DATABASE_URL:+set}"
echo "  Using DATABASE_URL fallback:  ${MIGRATION_DATABASE_URL:-set (fallback)}"
echo ""

# ── Activate virtual environment ──────────────────────────────────────
VENV="${MCP_DIR}/venv"
if [[ ! -f "${VENV}/bin/python" ]]; then
  echo "ERROR: venv not found at ${VENV}. Run: cd ${MCP_DIR} && python -m venv venv && pip install -r requirements.txt"
  exit 1
fi

# ── Check connectivity ────────────────────────────────────────────────
echo "[1/3] Checking database connectivity..."
"${VENV}/bin/python" -c "
import os, sys
from sqlalchemy import create_engine, text
url = os.environ.get('MIGRATION_DATABASE_URL') or os.environ.get('DATABASE_URL')
try:
    engine = create_engine(url, connect_args={} if 'postgresql' in url else {'check_same_thread': False})
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('  Database connection OK.')
except Exception as e:
    print(f'  FAIL: {e}')
    sys.exit(1)
"

# ── Show current revision before migration ────────────────────────────
echo "[2/3] Current Alembic revision..."
cd "${MCP_DIR}"
"${VENV}/bin/alembic" current

# ── Run migrations ────────────────────────────────────────────────────
echo "[3/3] Running alembic upgrade head..."
"${VENV}/bin/alembic" upgrade head

echo ""
echo "✓ Migrations complete. Head revision:"
"${VENV}/bin/alembic" current
