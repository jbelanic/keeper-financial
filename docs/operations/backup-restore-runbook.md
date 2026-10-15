# Keeper Financial — Backup, off-host copy, and restore runbook

- **Status:** owner-approved operational procedure (decision 49 P0 + owner direction 2026-10-14)
- **Scope:** daily automated backups, daily verified encrypted USB off-host copy, 30-day
  rolling retention, quarterly isolated restore drills, and alerting.
- **Scripts:** `scripts/backup_all.sh`, `scripts/backup_postgres.sh`,
  `scripts/backup_minio.py`, `scripts/backup_usb.sh`, `scripts/monitor_health.sh`,
  `scripts/send_alert.py`, `scripts/reconcile_restore_deletions.py`.

The target is simple and repeatable, not an enterprise backup platform. Low transaction
volume reduces the *workload*, not the need for the controls: a failed backup must be
*alerted*, and a backup that has never been restored is unproven.

## 0. Named operators (fill in before go-live)

| Role | Name | Responsibility |
| --- | --- | --- |
| Backup/monitor owner | ________ | Owns cron, reviews alerts, investigates failures |
| USB/off-host custodian | ________ | Performs the daily encrypted USB copy and rotation |
| Restore-drill operator | ________ | Runs quarterly restore drills and records results |
| Alert recipient (`ALERT_EMAIL`) | ________ | Receives failed-backup / monitor alerts |

A control performed by an unnamed person is not a control.

## 1. Daily automated backups (cron)

`scripts/backup_all.sh` runs the encrypted PostgreSQL dump (`backup_postgres.sh`) and the
MinIO mirror (`backup_minio.py`) at one consistency boundary. It exits non-zero on any
failure.

Install the cron entry (as root, edit `sudo crontab -e`):

```cron
# Daily coordinated Keeper backup at 02:10; alert on failure.
10 2 * * *  cd /srv/keeper-financial && ./scripts/backup_all.sh >> /var/log/keeper-backup.log 2>&1 || .venv/bin/python scripts/send_alert.py "Keeper backup FAILED" < /var/log/keeper-backup.log

# Hourly monitor at :17; alert on any critical failure.
17 * * * *  cd /srv/keeper-financial && ./scripts/monitor_health.sh > /var/log/keeper-monitor.log 2>&1 || .venv/bin/python scripts/send_alert.py "Keeper monitor FAILED" < /var/log/keeper-monitor.log
```

`backup_all.sh` writes to `BACKUP_POSTGRES_DIR` (default `/var/backups/keeper-postgres`)
and `BACKUP_MINIO_DIR` (default `/var/backups/keeper-minio`); the monitor checks those
same paths. Encryption: the PostgreSQL dump is encrypted with `openssl aes-256-cbc
-pbkdf2` when `BACKUP_ENCRYPTION_KEY_FILE` is set (keep that key file outside the repo and
outside the backup directory); MinIO objects are application-level ciphertext already.

**A failed or missing backup must generate an alert, not rely on someone noticing.** The
cron wrapper above pipes failure output to `scripts/send_alert.py`, which emails
`ALERT_EMAIL` through the configured SMTP relay (SMTP2GO). `monitor_health.sh` also
fails closed (non-zero) when the newest PostgreSQL/MinIO/USB backup is missing or older
than 26 hours, so a missed backup surfaces even if the backup job itself did not report.

## 2. Off-host encrypted USB copy (daily, two rotating drives)

A mirror on the same machine is not a recovery plan. Keep **two** LUKS-encrypted USB
drives, rotating daily so one is always off-site.

### 2.1 One-time drive preparation (per drive)

```bash
# Identify the device, then encrypt and format (DESTROYS the device).
sudo cryptsetup luksFormat /dev/sdX
sudo cryptsetup open /dev/sdX keeper-usb
sudo mkfs.ext4 /dev/mapper/keeper-usb
sudo cryptsetup close keeper-usb
```

Use a strong, separately-recorded LUKS passphrase. Never store it beside the drive or in
the repo.

### 2.2 Daily copy (performed by the named USB custodian)

```bash
# Mount the encrypted drive, copy + verify, unmount.
sudo cryptsetup open /dev/sdX keeper-usb
sudo mount /dev/mapper/keeper-usb "${USB_MOUNT:-/mnt/keeper-usb}"
sudo ./scripts/backup_usb.sh
sudo umount "${USB_MOUNT:-/mnt/keeper-usb}"
sudo cryptsetup close keeper-usb
```

`backup_usb.sh` copies the newest PostgreSQL dump and MinIO mirror, verifies them
(checksum + recursive diff), and writes a `last_success` marker that the monitor reads —
so a missed or failed USB copy is surfaced by `monitor_health.sh` just like any other
stale backup. Rotate to the other drive the next day and take it off-site.

## 3. Retention

- PostgreSQL dumps: 30-day rolling window (`backup_postgres.sh` deletes the oldest beyond
  30).
- MinIO mirrors: 30-day rolling window (`backup_minio.py`).
- USB drives: the two drives are the 30-day off-host copy; keep both until the next
  verified copy is written.
- Borrower key files: encrypted offline copies (separate from any backup) — `docs/37` §1.

## 4. Quarterly isolated restore drill (mandatory before real data)

A backup that has never been restored is unproven. Run this **quarterly**, and **before
accepting any real borrower data**, and record the outcome.

1. **Isolated target only** — restore into a separate container/namespace/directory, never
   over live data, with no production ingress.
2. **PostgreSQL** — restore the newest dump into a throwaway database:
   ```bash
   sudo sh -c "gunzip -c /var/backups/keeper-postgres/<newest>.sql.gz | docker compose -f /srv/keeper-financial/compose.yaml exec -T db psql -U keeper -d keeper_restore_test"
   ```
   (create `keeper_restore_test` first; adapt the custom-format path if the dump is
   custom-format).
3. **MinIO** — restore the mirror into an isolated bucket (never the live `keeper-private`).
4. **Reconcile** — run `scripts/reconcile_restore_deletions.py` with the backup timestamp
   so a restore cannot resurrect records deleted after the backup was taken.
5. **Verify** — confirm record↔object relationships reconcile and a representative
   document decrypts/downloads correctly through the API.
6. **Record** — append date, operator, backup timestamps, reconcile result, and any
   deviations to this runbook's log (below). Destroy the isolated target afterwards.

**Stop if**: the restore is incomplete, a checksum fails, reconcile reports a resurrection
conflict, or the drill can only pass by restoring into the live environment.

## 5. Alerting

| Condition | Mechanism |
| --- | --- |
| Backup job failed | cron wrapper → `send_alert.py` |
| Backup stale/missing (PG/MinIO/USB) | `monitor_health.sh` non-zero → cron wrapper → `send_alert.py` |
| Scanner unavailable/stale | `monitor_health.sh` (fail-closed in the upload path already) |
| Alert send fails | `send_alert.py` exit 1 is visible in cron output |

`send_alert.py` requires `ALERT_EMAIL` and the SMTP settings (`SMTP_HOST`,
`SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_TLS`) in `.env`.
Test the alert path after configuring it (trigger one deliberately).

## 6. Drill / incident log

| Date | Operator | Backup timestamps | Result | Notes |
| --- | --- | --- | --- | --- |
| | | | | |

## 7. What is intentionally out of scope

- Automated borrower **purge** and a seven-year retention engine (deferred, decision 49;
  the retention model is an open owner decision).
- Legal-hold API/UI (deferred; the `borrower_legal_holds` table exists but no apply/release
  operations).
- Automated candidate-document lifecycle management (manual, documented separately).
