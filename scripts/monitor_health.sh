#!/usr/bin/env bash
#
# Basic Keeper health monitor (decision 49 P0).
#
# Checks API/DB health, ClamAV availability, and PostgreSQL/MinIO backup
# freshness. Prints a digest and exits non-zero if any critical check fails.
# Run from cron; cron's MAILTO delivers the digest (and non-zero exit pages on
# failure). External reachability of public endpoints is a separate operator
# check (a probe on the same host cannot report that the host is down).
#
# Usage:
#   ./scripts/monitor_health.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Read the same deployment settings the backup scripts read, so the paths this
# monitor checks are always the paths the backups were written to.
# shellcheck source=lib/load_env.sh
. "${SCRIPT_DIR}/lib/load_env.sh"
keeper_load_env

FAILED=0

pass() { echo "PASS $1"; }
fail() { echo "FAIL $1"; FAILED=1; }

# 1. API liveness.
if curl -fsS --max-time 10 http://127.0.0.1:8000/health >/dev/null 2>&1; then
  pass "api /health"
else
  fail "api /health unreachable"
fi

# 2. Database reachability through the API.
if curl -fsS --max-time 10 http://127.0.0.1:8000/health/db >/dev/null 2>&1; then
  pass "api /health/db"
else
  fail "api /health/db unreachable"
fi

# 3. ClamAV readiness. A PING only proves clamd answers; the app needs a scan
#    decision and fresh signatures, so check all three.
CLAMD_PORT="${CLAMAV_MONITOR_PORT:-3310}"
CLAMD_MAX_SIGNATURE_AGE=604800 # 7 days; freshclam normally refreshes daily

# 3a. Liveness.
if exec 3<>"/dev/tcp/127.0.0.1/${CLAMD_PORT}" 2>/dev/null; then
  printf 'PING\n' >&3
  pong="$(head -c 4 <&3 2>/dev/null || true)"
  exec 3<&- 3>&-
  if [[ "$pong" == "PONG" ]]; then
    pass "clamd PING"
  else
    fail "clamd unexpected PING response"
  fi
else
  fail "clamd unavailable on 127.0.0.1:${CLAMD_PORT}"
fi

# 3b. A real INSTREAM scan of one byte. This exercises the same code path an
#     upload takes, so a scanner that answers PING but cannot scan is caught.
scan_reply=""
if exec 4<>"/dev/tcp/127.0.0.1/${CLAMD_PORT}" 2>/dev/null; then
  # zINSTREAM + NUL, 4-byte length (00000001), one byte of payload, 4-byte NUL terminator.
  printf '%b' 'zINSTREAM\000\000\000\000\001K\000\000\000\000' >&4 2>/dev/null
  IFS= read -r -d '' -t 10 scan_reply <&4 2>/dev/null || true
  exec 4<&- 4>&-
  scan_reply="${scan_reply//$'\r'/}"
  scan_reply="${scan_reply//$'\n'/}"
fi
if [[ "$scan_reply" == "stream: OK" ]]; then
  pass "clamd INSTREAM scan"
else
  fail "clamd INSTREAM scan: ${scan_reply:-no reply}"
fi

# 3c. Signature age, parsed from `VERSION` ("ClamAV <ver>/<sigs>/<date>").
version_reply=""
if exec 5<>"/dev/tcp/127.0.0.1/${CLAMD_PORT}" 2>/dev/null; then
  printf 'VERSION\n' >&5
  IFS= read -r -d '' -t 10 version_reply <&5 2>/dev/null || true
  exec 5<&- 5>&-
  version_reply="${version_reply//$'\r'/}"
  version_reply="${version_reply//$'\n'/}"
fi
signature_date="${version_reply##*/}"
if [[ -z "$version_reply" ]]; then
  fail "clamd VERSION unavailable"
elif signature_epoch="$(date -d "$signature_date" +%s 2>/dev/null)"; then
  signature_age=$(( $(date +%s) - signature_epoch ))
  if (( signature_age > CLAMD_MAX_SIGNATURE_AGE )); then
    fail "clamd signatures stale (${signature_age}s since ${signature_date})"
  else
    pass "clamd signatures fresh (${signature_date})"
  fi
else
  fail "clamd VERSION not parsed: ${version_reply}"
fi

# 4. Backup freshness: newest backup must be <= 26h old (24h + 2h slack).
_backup_age_seconds() { # $1 = directory, $2 = file pattern
  local newest
  newest="$(find "$1" -maxdepth 1 -type f -name "$2" -printf '%T@\n' 2>/dev/null \
    | sort -rn | head -n1 | cut -d. -f1)"
  if [[ -z "$newest" ]]; then
    echo ""
    return 0
  fi
  echo "$(( $(date +%s) - newest ))"
}

STALE_MAX=93600 # 26 hours in seconds

pg_dir="${BACKUP_POSTGRES_DIR:-/var/backups/keeper-postgres}"
pg_age="$(_backup_age_seconds "$pg_dir" 'keeper-*.sql.gz*')"
if [[ -z "$pg_age" ]]; then
  fail "no postgres backup found in $pg_dir"
elif (( pg_age > STALE_MAX )); then
  fail "postgres backup stale (${pg_age}s)"
else
  pass "postgres backup fresh"
fi

minio_dir="${BACKUP_MINIO_DIR:-/var/backups/keeper-minio}"
if [[ -d "$minio_dir" ]]; then
  newest_dir="$(find "$minio_dir" -maxdepth 1 -type d -name 'keeper-private-*' -printf '%T@ %p\n' 2>/dev/null \
    | sort -rn | head -n1)"
  if [[ -z "$newest_dir" ]]; then
    fail "no minio backup found in $minio_dir"
  else
    minio_age_s=$(( $(date +%s) - ${newest_dir%% *} ))
    if (( minio_age_s > STALE_MAX )); then
      fail "minio backup stale (${minio_age_s}s)"
    else
      pass "minio backup fresh"
    fi
  fi
else
  fail "minio backup dir missing: $minio_dir"
fi

# Off-host USB copy freshness: the daily USB step writes a success marker.
usb_marker="${USB_MOUNT:-/mnt/keeper-usb}/keeper-backups/last_success"
if [[ -f "$usb_marker" ]]; then
  usb_age_s=$(( $(date +%s) - $(stat -c %Y "$usb_marker") ))
  if (( usb_age_s > STALE_MAX )); then
    fail "usb backup stale (${usb_age_s}s)"
  else
    pass "usb backup fresh"
  fi
else
  fail "usb backup marker missing: $usb_marker"
fi

echo "---"
if (( FAILED )); then
  echo "MONITOR_FAIL $(date -u +%FT%TZ)"
  exit 1
fi
echo "MONITOR_OK $(date -u +%FT%TZ)"
