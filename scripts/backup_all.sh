#!/usr/bin/env bash
#
# Coordinated PostgreSQL + MinIO backup (decision 49 P0).
#
# Runs the encrypted PostgreSQL dump and the MinIO mirror at one consistency
# boundary and writes a combined manifest. Fails (non-zero) if either leg fails,
# so a cron wrapper can send an alert on backup failure.
#
# Usage:
#   ./scripts/backup_all.sh
#
# Environment (from .env): POSTGRES_DB, POSTGRES_USER, MINIO_ROOT_USER,
# MINIO_ROOT_PASSWORD, MINIO_BUCKET; optional BACKUP_ENCRYPTION_KEY_FILE.
# Destinations: BACKUP_POSTGRES_DIR (default /var/backups/keeper-postgres) and
# BACKUP_MINIO_DIR (default /var/backups/keeper-minio) — the same defaults the
# monitor (`monitor_health.sh`) and the runbook use.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "${SCRIPT_DIR}")"

PG_DIR="${BACKUP_POSTGRES_DIR:-/var/backups/keeper-postgres}"
MINIO_DIR="${BACKUP_MINIO_DIR:-/var/backups/keeper-minio}"
TS="$(date +%Y%m%dT%H%M%S)"

# Prefer the project venv for the Python MinIO mirror; fall back to python3.
PYTHON=""
if [[ -x "${COMPOSE_DIR}/.venv/bin/python" ]]; then
  PYTHON="${COMPOSE_DIR}/.venv/bin/python"
else
  PYTHON="python3"
fi

"${SCRIPT_DIR}/backup_postgres.sh" "${PG_DIR}"
"${PYTHON}" "${SCRIPT_DIR}/backup_minio.py" "${MINIO_DIR}"

echo "COORDINATED_BACKUP_OK ts=${TS} postgres=${PG_DIR} minio=${MINIO_DIR}"
