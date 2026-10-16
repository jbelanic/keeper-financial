# Keeper Financial — Isolated restore drill checklist

- **Purpose:** prove a backup actually restores. A backup that has never been restored
  is unproven.
- **When:** quarterly, and **before accepting real borrower data**.
- **Rule:** restore only into an **isolated** target — never over live data, no
  production ingress.

## 0. Pre-flight

- [ ] Operator recorded (see `local-notes/operators.md`).
- [ ] Newest backup present:
      `ls -la /var/backups/keeper-postgres /var/backups/keeper-minio`.
- [ ] Backup timestamp `TS` recorded from the newest filenames.
- [ ] Throwaway target names chosen (e.g. `keeper_restore_test` DB, a `keeper-restore-test`
      MinIO bucket) — never the live `keeper` DB or `keeper-private` bucket.

## 1. PostgreSQL restore (isolated)

The cron backup (`backup_postgres.sh`) is a **plain SQL** `pg_dump` gzipped
(`keeper-<TS>.sql.gz`, or `.sql.gz.enc` when encrypted).

```bash
cd /home/inspiron/keeper-financial
# Create a throwaway database (NOT the live 'keeper' database).
sudo docker compose exec -T db psql -U keeper -d postgres -c 'CREATE DATABASE keeper_restore_test;'

# Plain-format restore:
sudo sh -c "gunzip -c /var/backups/keeper-postgres/<newest>.sql.gz | \
  docker compose exec -T db psql -U keeper -d keeper_restore_test"

# Encrypted-format restore (decrypt first):
# sudo sh -c "openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 \
#   -pass file:/path/to/backup-key -in /var/backups/keeper-postgres/<newest>.sql.gz.enc | \
#   gunzip -c | docker compose exec -T db psql -U keeper -d keeper_restore_test"
```

> Note: `DEPLOYMENT_INSPIRON_STEP_BY_STEP.md` §20.1 also shows a manual `pg_dump
> --format=custom`. That custom-format dump restores with `pg_restore`, not
> `gunzip | psql`. This drill targets the **cron** backup, which is plain format.

## 2. MinIO restore (isolated)

There is **no restore script** — `backup_minio.py` mirrors *live → local* only. Restore
by copying the newest mirror into an isolated bucket (never `keeper-private`) using the
app's boto3/S3 stack against `http://127.0.0.1:9000`. Record the exact commands you use
in `local-notes/incident-log.md` so this step is repeatable.

## 3. Reconcile deletions (safety gate)

```bash
cd /home/inspiron/keeper-financial
.venv/bin/python scripts/reconcile_restore_deletions.py \
  --ledger <deletion-ledger.jsonl> --backup-time '<TS>'
```

`reconcile_restore_deletions.py` exits `1` on a resurrection conflict and `2` fail-closed
when the ledger is missing/malformed. If there is no deletion ledger yet, treat `--allow-missing-ledger`
as "not a clean pass" and record that explicitly.

## 4. Verify

- [ ] Record↔object relationships reconcile (no orphaned objects, no resurrected deletes).
- [ ] A representative document decrypts and downloads correctly through the API.
- [ ] The restored application row count matches the source at backup time.

## 5. Record and destroy

- [ ] Append date, operator, backup timestamps, reconcile result, and deviations to
      `local-notes/incident-log.md`.
- [ ] Destroy the isolated target (`DROP DATABASE keeper_restore_test;` and delete the
      test bucket) so no stray copy of production data persists.

## Stop conditions

Stop if: the restore is incomplete, a checksum fails, `reconcile_restore_deletions.py`
reports a resurrection conflict, or the drill can only pass by restoring into the live
environment.
