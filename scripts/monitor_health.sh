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

# 3. ClamAV availability via clamd PING on the loopback scanner port.
if exec 3<>/dev/tcp/127.0.0.1/3310 2>/dev/null; then
  printf 'PING\n' >&3
  pong="$(head -c 4 <&3 2>/dev/null || true)"
  exec 3<&- 3>&-
  if [[ "$pong" == "PONG" ]]; then
    pass "clamd PING"
  else
    fail "clamd unexpected PING response"
  fi
else
  fail "clamd unavailable on 127.0.0.1:3310"
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

echo "---"
if (( FAILED )); then
  echo "MONITOR_FAIL $(date -u +%FT%TZ)"
  exit 1
fi
echo "MONITOR_OK $(date -u +%FT%TZ)"
