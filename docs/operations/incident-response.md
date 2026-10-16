# Keeper Financial — Incident response runbook

- **Status:** owner-approved operational procedure; companion to `backup-restore-runbook.md`.
- **Scope:** detect, triage, contain, recover, and learn from operational incidents on `inspiron`.
- **Operator:** the single `sudo` administrator. Real names/contacts live in
  `local-notes/operators.md` (gitignored) — never in this tracked file.

## 1. Severity

| Severity | Definition | Response |
| --- | --- | --- |
| SEV1 | Public borrower/agent site down, data loss, or suspected compromise | Immediate (stop-the-line) |
| SEV2 | A component down while service still up (e.g. ClamAV down → uploads fail closed), or backup/alerting failing | Within the hour |
| SEV3 | Degraded / non-blocking (cosmetic, slow, one stale backup) | Next business day |

Fail-closed behaviour is **not** a SEV1 by itself: when ClamAV or MinIO is down,
uploads/submission reject cleanly rather than accepting unscanned data — that is the
system working as designed. Restoring the component is still a SEV2.

## 2. Detection

- `scripts/monitor_health.sh` (hourly cron) emails `ALERT_EMAIL` via `send_alert.py` on any FAIL.
- `scripts/backup_all.sh` (daily cron) emails on backup failure.
- User/agent reports.
- Liveness probes: `curl -fsS http://127.0.0.1:8000/health` and `/health/db`.

On any alert, first read `/var/log/keeper-monitor.log` and `/var/log/keeper-backup.log`.

## 3. Procedure

### 3.1 Detect & acknowledge
Record the time, the alert, and which check failed.

### 3.2 Triage
```bash
cd /home/inspiron/keeper-financial
sudo docker compose ps --all
curl -fsS http://127.0.0.1:8000/health; echo
curl -fsS http://127.0.0.1:8000/health/db; echo
sudo docker compose logs --tail=100 api
```

### 3.3 Contain
Stop the bleeding before fixing. For a suspected compromise or data exposure, stop the
affected service and preserve evidence (`docker logs`, `/var/log/nginx/`). **Never** run
`docker compose down --volumes`, `docker volume rm`, or `git reset --hard` during an
incident.

### 3.4 Recover
Use the per-service playbooks below, then re-run `./scripts/monitor_health.sh` and the
health probes after each change.

### 3.5 Post-incident
Append a dated entry to `local-notes/incident-log.md` (timeline, root cause, what you
changed, follow-ups). An unlogged incident is an unreviewed control.

## 4. Per-service playbooks

### 4.1 API down (`/health` fails)
1. `sudo docker compose ps --all` — is `api` up, exited, or restarting?
2. `sudo docker compose logs --tail=200 api` — the crash reason.
3. Fix config/code, then `sudo docker compose up -d api` (add `--build` if code changed).
4. `curl -fsS http://127.0.0.1:8000/health`.

### 4.2 Database down (`/health/db` fails)
1. `sudo docker compose ps --all` and `sudo docker compose logs db`.
2. Restart only: `sudo docker compose restart db`.
3. If the volume is corrupt, this is a SEV1: restore the newest backup into an
   **isolated** target first (see `restore-drill.md`) before touching live data.

### 4.3 ClamAV down (uploads reject fail-closed)
1. `sudo docker compose ps clamav` and `sudo docker compose logs clamav`.
2. `./scripts/monitor_health.sh` — its `clamd PING` check confirms the scanner.
3. `sudo docker compose restart clamav`, then refresh signatures if the image exposes
   `freshclam`.
4. Re-run `./scripts/monitor_health.sh`.

### 4.4 MinIO storage down (uploads/submission 503)
1. `sudo docker compose ps minio` and `sudo docker compose logs minio`.
2. `sudo docker compose restart minio`.
3. Confirm: `curl -fsS http://127.0.0.1:9000/minio/health/live`.

### 4.5 Backup failed or stale
1. Read `/var/log/keeper-backup.log`.
2. Re-run `sudo ./scripts/backup_all.sh` and fix the leg it reports (disk full → prune
   old dumps; MinIO creds → check `.env`).
3. If `send_alert.py` itself failed, fix `SMTP_*` / `ALERT_EMAIL` in `.env` and test
   with a deliberate alert.

### 4.6 Nginx / ingress down
1. `sudo nginx -t`, then `sudo systemctl status nginx`.
2. If config broken, restore `infrastructure/nginx/` plus your `/etc/nginx` backup,
   then `sudo nginx -t && sudo systemctl reload nginx`.
3. Hairpin NAT: on-host `curl https://…` can hang — verify externally or with
   `curl --resolve <domain>:443:127.0.0.1 https://<domain>/`.

### 4.7 Hosted Supabase Auth down (external)
Identity depends on Supabase. There is no local remediation; confirm the outage on
Supabase's status page and alert users. Application data and authorization are
unaffected (the application database remains authoritative).

### 4.8 Alert email (SMTP2GO) down
Run `echo test | .venv/bin/python scripts/send_alert.py "alert-path test"`. On failure,
check `.env` SMTP settings and SMTP2GO status. A down alert path is a SEV2 — you lose
visibility into every other failure.

## 5. Stop criteria

Stop and escalate (or restore from backup) if:

- you cannot explain why a service failed,
- a data-destroying action (`down --volumes`, `volume rm`, `git reset --hard`) looks necessary,
- the failure is a suspected compromise — preserve evidence, do not "fix" over it,
- restore is the only path — follow `restore-drill.md`, and never into live data.
