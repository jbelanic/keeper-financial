#!/usr/bin/env bash
#
# Encrypted PostgreSQL backup (decision 49 P0).
#
# Dumps the application database through the `db` service (postgres:17-alpine,
# which runs on the target host), gzip-compresses, and — when
# BACKUP_ENCRYPTION_KEY_FILE is set — encrypts with openssl AES-256-CBC/PBKDF2.
# The key file must live outside the repo and outside the backup destination
# (crown-jewels custody). No password is placed on the command line: pg_dump
# runs inside the db container, which already holds POSTGRES_PASSWORD.
#
# Usage:
#   ./scripts/backup_postgres.sh [DEST_DIR]
#
# Environment (loaded from $KEEPER_ENV_FILE or <repo>/.env): POSTGRES_DB,
# POSTGRES_USER; optional BACKUP_ENCRYPTION_KEY_FILE.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "${SCRIPT_DIR}")"

# shellcheck source=lib/load_env.sh
. "${SCRIPT_DIR}/lib/load_env.sh"
keeper_load_env

DEST_DIR="${1:-${BACKUP_DIR:-/var/backups/keeper-postgres}}"
DB_NAME="${POSTGRES_DB:-keeper}"
DB_USER="${POSTGRES_USER:-keeper}"
TS="$(date +%Y%m%dT%H%M%S)"
PLAIN="${DEST_DIR}/keeper-${TS}.sql.gz"
OUT="${PLAIN}"

mkdir -p "${DEST_DIR}"

# pg_dump inside the db container; pipefail fails the script on any dump/gzip error.
(
  cd "${COMPOSE_DIR}"
  docker compose exec -T db pg_dump -U "${DB_USER}" -d "${DB_NAME}"
) | gzip > "${PLAIN}"

if [[ ! -s "${PLAIN}" ]]; then
  echo "BACKUP_FAIL db=${DB_NAME} empty dump" >&2
  exit 1
fi

if [[ -n "${BACKUP_ENCRYPTION_KEY_FILE:-}" ]]; then
  openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 \
    -pass "file:${BACKUP_ENCRYPTION_KEY_FILE}" \
    -in "${PLAIN}" -out "${PLAIN}.enc"
  rm -f "${PLAIN}"
  OUT="${PLAIN}.enc"
else
  # Not an error — encryption is opt-in — but it must never be silent: this dump
  # contains borrower personal information.
  echo "BACKUP_WARN db=${DB_NAME} unencrypted (BACKUP_ENCRYPTION_KEY_FILE is not set)" >&2
fi

SIZE="$(stat -c%s "${OUT}")"
echo "BACKUP_OK db=${DB_NAME} dest=${OUT} bytes=${SIZE}"

# Rolling 30-day retention (keep the newest 30 dumps).
find "${DEST_DIR}" -maxdepth 1 -type f -name 'keeper-*.sql.gz*' -printf '%T@ %p\n' \
  | sort -rn | tail -n +31 | cut -d' ' -f2- | xargs -r rm -f
