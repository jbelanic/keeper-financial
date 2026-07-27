#!/usr/bin/env bash
#
# Minimal Keeper MinIO backup (free, no install).
#
# Mirrors the private bucket to a local directory using the minio/mc container
# image. Requires only Docker. No credentials are written to logs beyond the
# restricted evidence boundary; object keys/signed URLs are not echoed.
#
# Usage:
#   ./scripts/backup_minio.sh [DEST_DIR]
#
# Environment (from .env): MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD
set -euo pipefail

DEST_DIR="${1:-${BACKUP_DIR:-/var/backups/keeper-minio}}"
BUCKET="${MINIO_BUCKET:-keeper-private}"
ENDPOINT="${MINIO_ENDPOINT:-http://127.0.0.1:9000}"
USER="${MINIO_ROOT_USER:?MINIO_ROOT_USER required}"
PASS="${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD required}"
ALIAS="keeperlocal"
TS="$(date +%Y%m%dT%H%M%S)"
OUT="${DEST_DIR}/${BUCKET}-${TS}"

mkdir -p "${DEST_DIR}"

# Run mc inside a throwaway container with the host MinIO reachable.
docker run --rm --network host \
  -v "${DEST_DIR}:/backup" \
  minio/mc \
  sh -c "
    mc alias set ${ALIAS} '${ENDPOINT}' '${USER}' '${PASS}' >/dev/null &&
    mc mirror --overwrite --watch=false ${ALIAS}/${BUCKET} /backup/${BUCKET}-${TS} >/dev/null &&
    echo \"BACKUP_OK bucket=${BUCKET} dest=/backup/${BUCKET}-${TS}\"
  "

# Manifest: object count + total bytes (no keys/URLs).
COUNT="$(find "${OUT}" -type f | wc -l)"
echo "MANIFEST ts=${TS} bucket=${BUCKET} objects=${COUNT} dest=${OUT}"

# Retention: keep last 30 daily backups (rolling 30-day default).
find "${DEST_DIR}" -maxdepth 1 -type d -name "${BUCKET}-*" -printf '%T@ %p\n' \
  | sort -rn | tail -n +31 | cut -d' ' -f2- | xargs -r rm -rf
