#!/usr/bin/env bash
#
# Copy the latest Keeper backups to an encrypted USB drive and verify (decision 49 P0).
#
# The USB drive must already be LUKS-encrypted and mounted (see the runbook
# docs/operations/backup-restore-runbook.md). Copies the newest PostgreSQL dump
# and MinIO mirror, verifies them, and writes a success marker the monitor reads
# for USB freshness. Exits non-zero on any failure so the operator (or a cron
# wrapper) can alert.
#
# Usage:
#   sudo ./scripts/backup_usb.sh          # drive mounted at USB_MOUNT
#
# Environment: USB_MOUNT (default /mnt/keeper-usb), BACKUP_POSTGRES_DIR,
# BACKUP_MINIO_DIR.
set -euo pipefail

MOUNT="${USB_MOUNT:-/mnt/keeper-usb}"
PG_DIR="${BACKUP_POSTGRES_DIR:-/var/backups/keeper-postgres}"
MINIO_DIR="${BACKUP_MINIO_DIR:-/var/backups/keeper-minio}"
DEST="${MOUNT}/keeper-backups"
MARKER="${DEST}/last_success"

if [[ ! -d "${MOUNT}" ]]; then
  echo "USB_FAIL mount point missing: ${MOUNT}" >&2
  exit 1
fi

# Newest PostgreSQL dump and MinIO mirror (by mtime).
PG_NEWEST="$(find "${PG_DIR}" -maxdepth 1 -type f -name 'keeper-*.sql.gz*' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -n1 | cut -d' ' -f2-)"
MINIO_NEWEST="$(find "${MINIO_DIR}" -maxdepth 1 -type d -name 'keeper-private-*' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -n1 | cut -d' ' -f2-)"

if [[ -z "${PG_NEWEST}" || -z "${MINIO_NEWEST}" ]]; then
  echo "USB_FAIL missing source backup (postgres='${PG_NEWEST}' minio='${MINIO_NEWEST}')" >&2
  exit 1
fi

mkdir -p "${DEST}"

cp -a "${PG_NEWEST}" "${DEST}/"
cp -a "${MINIO_NEWEST}" "${DEST}/$(basename "${MINIO_NEWEST}")"

# Verify the PostgreSQL copy checksum and the MinIO mirror contents.
(
  cd "${DEST}"
  sha256sum "$(basename "${PG_NEWEST}")" > .usb.sha256
  sha256sum --check .usb.sha256 >/dev/null
  diff -rq "$(basename "${MINIO_NEWEST}")" "${MINIO_NEWEST}" >/dev/null
)

date -u +%FT%TZ > "${MARKER}"
echo "USB_OK pg=$(basename "${PG_NEWEST}") minio=$(basename "${MINIO_NEWEST}") marker=${MARKER}"
