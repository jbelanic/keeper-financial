# Minimal Operational Readiness (free, low-maintenance)

- **Date:** 2026-07-27
- **Status:** owner-directed minimal implementations for the five operational-readiness items; not a substitute for the full Phase 1F evidence plan (`docs/26`)
- **Principle:** free, simple to maintain, no new vendors or infrastructure

This document records the minimal, free implementations for the five operational-readiness
items requested on 2026-07-27. Each item is intentionally the smallest safe step; the
comprehensive evidence work in `docs/26` remains the path to a controlled pilot or production
evidence package. On 2026-07-30 the owner provided explicit deploy/release and "deploy now"
approval for the self-hosted Keeper replacement on target Ubuntu host `inspiron`. That approval
removes the prior missing-owner-approval deployment gate; it does not weaken the secure-runtime,
firewall, TLS, private MinIO, fail-closed ClamAV, local Supabase Auth, backup/restore, logging,
or non-destructive cutover requirements below.

## 1. Key custody (borrower encryption keyring + capability HMAC key)

The borrower application requires two secret files supplied outside Git from root-owned
read-only files (or an equivalent deployment secret mount):

- `BORROWER_ENCRYPTION_KEYRING_FILE` — AES-256-GCM versioned keyring. Local format:
  `{"version": 1, "keys": {"001": "<base64 32-byte key>"}}`. The active key id is
  `BORROWER_ENCRYPTION_ACTIVE_KEY_ID` (default `001`).
- `BORROWER_CAPABILITY_HMAC_KEY_FILE` — 32 raw bytes used as the keyed digest for borrower
  capabilities.

### Local bootstrap (already performed for the local stack)
Secrets are generated into `secrets/` (gitignored) and bind-mounted into the API container
at `/run/secrets` by the tracked Compose API service. Local operator commands that need the
application database, including `make seed` and `make link-local-admin`, run inside the API
container so they use the same Docker database URL and secret mounts as the running API. The
secret files are never committed.

### Backup / restore (free)
- Copy both files to an encrypted offline location. Treat them as the crown jewels: anyone
  with the keyring can decrypt borrower SIN and financial data.
- Restore: place the files back at the configured paths with the same root-owned,
  read-only (mode `0400`) permissions. The API requires them at startup; missing or
  symlinked/unhardlinked files fail closed.

### Rotation (manual, dual-write)
1. Add a new key id to the keyring JSON (e.g., `002`) with a fresh 32-byte key; keep `001`
   available for reads.
2. Set `BORROWER_ENCRYPTION_ACTIVE_KEY_ID=002` so new writes use the new key.
3. Old ciphertext remains decryptable with `001` until a separately approved re-encryption
   and retirement operation completes; only then remove `001`.
4. Rotate the HMAC key only during a maintenance window with no in-flight capability
   issuance, because existing capability digests depend on it.
- No in-place key edit; never reuse a retired key id.

## 2. MinIO backup and isolated restore

Bucket: `keeper-private` (candidate + borrower private objects). Supabase Storage remains
disabled; MinIO is the only object store.

### Minimal backup (free)
`scripts/backup_minio.sh` mirrors the bucket to a local directory using the `minio/mc`
container (no install required). Run on a schedule (cron / systemd timer):

```bash
./scripts/backup_minio.sh /var/backups/keeper-minio
```

It requires `MINIO_ENDPOINT`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` (from `.env`) and
writes a timestamped mirror plus a manifest. It does not store object keys or signed URLs in
logs beyond the restricted evidence boundary.

### Restore test (isolated)
1. Restore into a separate bucket/target that is not reachable from the live application.
2. Reconcile object keys against PostgreSQL metadata; any orphan is recorded, not copied
   into live.
3. Destroy the isolated target after the check (or retain per the approved backup policy).

## 3. ClamAV signature freshness, health, and fail-closed

- Image `clamav/clamav:stable` runs `clamd` (port 3310, internal only) and `freshclam`.
- Health is asserted by `clamdcheck.sh` (compose healthcheck); the API connects with a
  2s connect / 15s read timeout.
- Fail-closed is enforced in code: a scanner timeout, malformed response, unavailable daemon,
  or non-clean result persists **no** MinIO bytes and **no** PostgreSQL document metadata.
- Freshness: `freshclam` updates signatures from the public mirror by default. For local
  operation, add a periodic check (cron) that records engine + signature version/age and
  alerts if age exceeds the approved threshold (default: 24h). No new service is required;
  a one-line cron calling `docker exec keeper-financial-clamav-1 freshclam --quiet` and
  logging the result is sufficient for local evidence.

## 4. DNS / TLS / ingress (local done; production requirements)

Local stack uses loopback / self-signed origins; production security is not weakened for
local testing. Approved production topology (owner decision 2026-07-24, `OD-04`):

- `https://keeperfinancial.ca/apply` — public entry/choice page.
- `https://apply.keeperfinancial.ca` — dedicated borrower origin from the same release.
- Caddy is the approved self-hosted ingress: exact-host routing, HTTPS termination,
  HTTP→HTTPS redirect.
- Only the ingress exposes public 80/443. API, PostgreSQL, MinIO, ClamAV, Supabase Studio,
  MinIO Console, and provider admin surfaces stay on private container networks or loopback.
- CORS/CSRF origins are exact; wildcards and reflected origins prohibited.
- Production borrower cookies: secure, HTTP-only, host-only, same-site strict, narrowly
  scoped, rotated as required, omitted from logs.
- Forwarded-host/proto/client-IP trusted only from the configured ingress.
- Security headers, `no-store`, request-size limits, timeouts, rate limits, and bot
  mitigation required before public exposure.

These remain documented requirements; the operational DNS/TLS/Caddy configuration and
firewall evidence are `docs/26` RF-04/RF-06 items. The approved side-by-side and cutover
runbook is `docs/DEPLOYMENT_SIDE_BY_SIDE.md`; it keeps WordPress public until cutover,
keeps Keeper internals loopback-only, and uses the reviewed Caddy template at
`infrastructure/caddy/Caddyfile` only during the explicit cutover step.

## 5. Production Auth email + logging / PII safety

### Transactional email (SMTP added)
- `SMTP_ENABLED`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_FROM`, `SMTP_PASSWORD`
  (see `docs/11_ENVIRONMENT_VARIABLES.md` and `.env.example`) configure outbound mail.
- The local stack can use Supabase Mailpit on `127.0.0.1:54324` / `host.docker.internal:54324`
  with no new service. That endpoint is Mailpit's HTTP capture/API surface; local lead
  notifications use Mailpit's HTTP send API before SMTP fallback. Production uses a configured
  transactional provider.
- Borrower notifications (`services/borrower_notifications.py`) never include PII in the
  message body and fail non-fatally (email delivery is best-effort and never blocks a
  submission or assignment).

### Logging / PII safety (by construction)
- Structured JSON logs (`core/logging.py`) carry only safe fields: timestamp, level,
  logger, message, and explicit extra attributes. No global redactor exists; safety comes
  from never logging SIN, capability values, plaintext payloads, keys, document contents,
  filenames, object URLs, or tokens. Audit events (`docs/28` §12) record only opaque IDs,
  actor, action, result, bounded reason/category, version, and timestamp.
- `middleware/sensitive_uploads.py` bounds and authenticates multipart bodies before parsing.
- Gap / hardening note: a global outbound log-redaction filter is a recommended later
  hardening step but is not required for the minimal local launch. The fail-closed rule
  stands regardless: any token/cookie/private URL/SIN/payload in logs is a stop condition
  under `docs/26` RF-10.

## Accessibility (incorporated, not a release blocker)

The public accessibility statement lives at `apps/web/app/(public)/accessibility/page.tsx`
and describes Keeper's approach (semantic structure, keyboard operation, visible focus,
labelled fields, reflow, non-colour status, contrast, reduced motion, alt text, feedback
contacts, alternative formats). On 2026-07-27 the owner directed that accessibility is
incorporated into the site and is not a standalone release blocker; the formal specialist
accessibility review remains a deferred production-gate item recorded in `docs/26` (OD-16 /
RF-17), consistent with the owner's separate deploy decision.

## Pilot go/no-go

On 2026-07-27 the owner directed that mandatory pilot go/no-go criteria are not required as
a gate before the owner's separate deployment decision. The comprehensive pilot criteria in
`docs/26` §9 remain available as a planning aid but are not enforced as blockers. On 2026-07-30
the owner provided explicit "deploy now" approval for the self-hosted replacement on target host
`inspiron`. Approved wording, minimal readiness, accessibility incorporation, and deploy approval
permit deployment execution, but real-borrower submission still requires successful deployed
runtime evidence and the implemented release controls: borrower application enabled, real-data
enabled, and the active consent-catalog row's server-owned `real_data_approved=true` marker for
the exact approved consent version/digest.
