#!/usr/bin/env bash
#
# Coordinated PostgreSQL + MinIO backup (decision 49 P0).
#
# Runs the encrypted PostgreSQL dump and the MinIO mirror at one consistency
# boundary and writes a combined manifest. Fails (non-zero) if either leg fails,
# so a cron/MAILTO wrapper can alert on backup failure.
#
# Usage:
#   ./scripts/backup_all.sh [DEST_DIR]
#
# Environment (from .env): POSTGRES_DB, POSTGRES_USER, MINIO_ROOT_USER,
# MINIO_ROOT_PASSWORD, MINIO_BUCKET; optional BACKUP_ENCRYPTION_KEY_FILE.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "${SCRIPT_DIR}")"

DEST_DIR="${1:-${BACKUP_DIR:-/var/backups/keeper}}"
TS="$(date +%Y%m%dT%H%M%S)"

# Prefer the project venv for the Python MinIO mirror; fall back to python3.
PYTHON=""
if [[ -x "${COMPOSE_DIR}/.venv/bin/python" ]]; then
  PYTHON="${COMPOSE_DIR}/.venv/bin/python"
else
  PYTHON="python3"
fi

"${SCRIPT_DIR}/backup_postgres.sh" "${DEST_DIR}/postgres"
"${PYTHON}" "${SCRIPT_DIR}/backup_minio.py" "${DEST_DIR}/minio"

echo "COORDINATED_BACKUP_OK ts=${TS} postgres=${DEST_DIR}/postgres minio=${DEST_DIR}/minio"
