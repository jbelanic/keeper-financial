# Deployment account model — single `sudo` administrator

- **Audience:** the server administrator.
- **Model:** one `sudo`-capable administrator account performs every deployment and
  operational step directly — Git, Docker, Nginx, Certbot, backups, and monitoring.
  There is **no** separate restricted `keeper-deploy` account.
- **Deployment directory:** `/home/inspiron/keeper-financial`, owned by that administrator.

## Why a single account

The earlier two-account model (a restricted `keeper-deploy` account plus a separate
`sudo` operator) was replaced with a single administrator because the target host is
administered directly over SSH by one person who already has `sudo`. Docker access on
this account is root-equivalent, so protect it accordingly (strong SSH key/password,
MFA where available).

## What this means for the runbook

- Every command in `docs/DEPLOYMENT_INSPIRON_STEP_BY_STEP.md` runs as `[SON/ROOT]`
  with `sudo`.
- There is no `[DEPLOY]` label and no `sudo -u keeper-deploy` prefix.
- The deployment path is `/home/inspiron/keeper-financial`.

## Guardrails (unchanged)

- Never commit `.env`, `secrets/`, or signing keys (already gitignored).
- Never force-push or rewrite history.
- Run backups and monitoring exactly as described in
  `docs/operations/backup-restore-runbook.md`; record private operator names in
  `local-notes/` (gitignored), not in the tracked runbooks.
