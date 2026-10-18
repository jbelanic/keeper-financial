# Keeper Financial — self-hosted Documenso production deployment

- **Status:** owner-approved operational procedure (decision 10 + 49 follow-up; esign is day-one critical)
- **Topology:** Documenso runs on the **same** `inspiron` host, behind the existing
  host-managed Nginx, at `https://sign.keeperfinancial.ca`. It is **not** part of Keeper's
  `compose.yaml`; it is its own Compose project (`/home/john/dev/documenso` or the
  deployment equivalent). Keeper connects to it over HTTPS via the configured adapter.

The Keeper application is already code-ready: the production validator requires
`DOCUMENSO_API_BASE_URL` to be an exact HTTPS `/api/v2` origin and `DOCUMENSO_PUBLIC_BASE_URL`
to be exactly `https://sign.keeperfinancial.ca`. This runbook is the missing deployment side.

## 0. Named operator

| Role | Name | Responsibility |
| --- | --- | --- |
| Documenso operator | ________ | Owns the Documenso stack, its DB, and signing keys |
| Signing-key custodian | ________ | Backs up `cert.p12` + passphrase; owns rotation |

## 1. Port map (already collision-free — keep it this way)

Your Documenso compose already avoids colliding with Keeper:

| Service | Binding | Collision with Keeper? |
| --- | --- | --- |
| Documenso app | `127.0.0.1:3001` | No (Keeper web is `:3000`) |
| Documenso Postgres | internal only | No (Keeper db is `127.0.0.1:5432`) |
| Documenso Redis | internal only | No |
| Documenso Mailpit | `127.0.0.1:1025/8025` | No |

Keep Postgres/Redis internal. Do **not** publish them to the host.

## 1.1 Host CPU baseline (verified requirement)

The published `documenso/documenso` image will not run on a CPU without SSE4.2/AVX. Two native
addons abort with SIGILL (`Illegal instruction`, exit 132) and the app container restart-loops
before it serves a single request:

| Module | Consequence |
| --- | --- |
| `@img/sharp-linuxmusl-x64` (libvips) | `rc=132` on dlopen |
| `@napi-rs/canvas-linux-x64-musl` (Skia) | `rc=132` on dlopen |

Both are in the document render/sign path, so there is no "disable it" workaround: an
uncaught SIGILL cannot be caught from JavaScript.

Preflight the target host **before** pulling anything:

```bash
grep -m1 -o -E 'sse4_2|avx' /proc/cpuinfo || echo "HOST UNSUPPORTED — provision a newer CPU"

docker run --rm --entrypoint sh documenso/documenso@sha256:945bd2c04306bd5d78def0c4ceafdffb6b0a106cd6a2543db5acda9a6424b2d9 -c '
find /app/node_modules -name "*.node" -path "*musl*" | while read f; do
  node -e "process.dlopen({exports:{}},\"$f\")" >/dev/null 2>&1
  echo "rc=$? $f"
done' | grep -v 'rc=0'
```

No output from the second command is a pass; any `rc=132` means that addon cannot execute on
this host.

Diagnosis notes from a verified failure (AMD Athlon II X4 630, 2009):

- Plain `node` works — both `node:22-alpine` and the image's own `node -e` succeed — so the
  failure is additive, not Node itself.
- The Prisma engine loads and `prisma migrate deploy` succeeds, so migrations apply and the
  first-run output looks healthy right up to `🌟 Starting Documenso server...`.
- `docker inspect` can report a clean-looking exit while the container is cycling under
  `restart: unless-stopped`, so restart loops must be diagnosed from `logs` and a foreground
  run (`--entrypoint sh app -c 'node build/server/main.js'`), not from the exit code alone.

## 2. Production hardening (required before public exposure)

The Documenso `docker-compose.yaml` ships development defaults. Before `sign.keeperfinancial.ca`
is public, replace every one of these with a strong, separately-recorded secret:

- `POSTGRES_PASSWORD` (currently `documenso`) → strong random.
- `NEXTAUTH_SECRET`, `NEXT_PRIVATE_ENCRYPTION_KEY`, `NEXT_PRIVATE_ENCRYPTION_SECONDARY_KEY`,
  `NEXT_PRIVATE_SIGNING_PASSPHRASE` (all hardcoded) → strong random (e.g. `openssl rand -hex 32`).
- Pin images: `documenso/documenso:latest` and `axllent/mailpit:latest` → pinned digest/tag.
  The tracked stack in §2.1 already pins Postgres, Redis, and the Documenso app by digest and
  omits Mailpit entirely; do not reintroduce `latest`.

**Signing certificate** (`certificates/cert.p12` + its passphrase): this is the Documenso
signing identity. Back it up as a crown jewel — losing it breaks re-verification of past
signed documents. Treat it like the Keeper borrower keyring (`docs/37` §1).

**Email:** replace Mailpit with the approved transactional provider (SMTP2GO). In the
Documenso compose environment, set:

```dotenv
NEXT_PRIVATE_SMTP_TRANSPORT=smtp-auth
NEXT_PRIVATE_SMTP_HOST=mail.smtp2go.com
NEXT_PRIVATE_SMTP_PORT=2525            # or 587 (STARTTLS); 465 needs secure=true
NEXT_PRIVATE_SMTP_SECURE=false         # false = STARTTLS on 2525/587
NEXT_PRIVATE_SMTP_USER=<smpt2go username>
NEXT_PRIVATE_SMTP_PASSWORD=<smpt2go SMTP password>
NEXT_PRIVATE_SMTP_FROM_NAME=Keeper Financial
NEXT_PRIVATE_SMTP_FROM_ADDRESS=no-reply@keeperfinancial.ca
```

Mailpit may be removed from the production stack entirely.

### 2.1 Tracked stack definition

The production Compose project is version-controlled in this repository, not in the upstream
Documenso checkout:

| Path | Purpose |
| --- | --- |
| `infrastructure/documenso/docker-compose.production.yaml` | Pinned-digest stack: app on `127.0.0.1:3001`, internal Postgres/Redis, no Mailpit, no secret literals |
| `infrastructure/documenso/env.production.example` | Non-secret configuration — installed as `.env` |
| `infrastructure/documenso/secrets.production.example` | Required secret keys and their generation commands — installed output is `.secrets.env` |

Install and run it from the deployment directory, because its relative paths (`./certificates`,
`.env`, `.secrets.env`) resolve against the working directory:

```bash
sudo mkdir -p /home/inspiron/documenso
sudo install -m 0644 infrastructure/documenso/docker-compose.production.yaml \
  /home/inspiron/documenso/docker-compose.yaml
cd /home/inspiron/documenso
sudo docker compose config --quiet   # requires .env and .secrets.env to exist
sudo docker compose up -d
```

Do not run this file from inside the repository checkout: the relative paths would resolve to
the checkout instead of the deployment directory.

`certificates/cert.p12` must be owned by the uid the image runs as. The image's user is
`nodejs`, **uid 1001**, and the file is mode `0400`, so a root-owned bundle is unreadable to
the container: Documenso boots with "Certificate not found or not readable" and signing
disabled, without failing the container. After generating the bundle:

```bash
chown 1001:1001 /home/inspiron/documenso/certificates/cert.p12
chmod 0400 /home/inspiron/documenso/certificates/cert.p12
```

Keep `0400` — do not relax it to `0444` to make the container read it.


## 3. Public URLs and DNS/TLS

- Real DNS: `sign.keeperfinancial.ca` → `inspiron`.
- Set the Documenso public URLs to the production origin and recreate the app:

```dotenv
NEXTAUTH_URL=https://sign.keeperfinancial.ca
NEXT_PUBLIC_URL=https://sign.keeperfinancial.ca
NEXT_PUBLIC_API_URL=https://sign.keeperfinancial.ca
NEXT_PUBLIC_WEBAPP_URL=https://sign.keeperfinancial.ca
NEXT_PRIVATE_INTERNAL_WEBAPP_URL=http://127.0.0.1:3001
```

`NEXT_PRIVATE_INTERNAL_WEBAPP_URL` is the URL the app uses to call **itself** — the local
job scheduler dispatches to `${NEXT_PRIVATE_INTERNAL_WEBAPP_URL}/api/jobs/...`
(`packages/lib/jobs/client/local.ts`). It must be reachable from inside the container, so it
is the loopback port, not the public origin. Upstream's own `.env.example` documents it as
"URL used by the web app to request itself (e.g. local background jobs)" and defaults it to
`http://localhost:3000`. Pointing it at `https://sign.keeperfinancial.ca` requires DNS
hairpin from the container plus the certificate to already be live; when the self-call fails
the scheduler crashes and the container restart-loops even though the certificate and
database are fine.

- Obtain a Let's Encrypt certificate for `sign.keeperfinancial.ca` using the host's existing
  Certbot, then install the reviewed server block `infrastructure/nginx/documenso-financial.conf`
  (proxies `127.0.0.1:3001` with WebSocket upgrade):

```bash
sudo install -m 0644 infrastructure/nginx/documenso-financial.conf /etc/nginx/sites-available/documenso-financial.conf
sudo ln -s /etc/nginx/sites-available/documenso-financial.conf /etc/nginx/sites-enabled/documenso-financial.conf
sudo nginx -t
sudo systemctl reload nginx
curl -I https://sign.keeperfinancial.ca/
```

Issue the certificate **before** installing that server block: it references
`/etc/letsencrypt/live/sign.keeperfinancial.ca/{fullchain,privkey}.pem`, which do not exist
until issuance, so `nginx -t` fails if the block is installed first. Install a temporary
port-80-only server block that serves `/.well-known/acme-challenge/` from `/var/www/certbot`,
issue with `certbot certonly --webroot -w /var/www/certbot -d sign.keeperfinancial.ca`, then
install the reviewed block and remove the temporary one. Do not use `certbot --nginx`, which
rewrites the reviewed configuration.

## 4. ICA template and signer recipient

In the Documenso UI, create the approved **ICA** template and note:

- the numeric **template id** → Keeper `DOCUMENSO_ICA_TEMPLATE_ID`;
- the **signer recipient id** for the candidate → `DOCUMENSO_ICA_SIGNER_RECIPIENT_ID`.

Create a Documenso **API token** → Keeper `DOCUMENSO_API_TOKEN`.

## 5. Keeper `.env` on `inspiron`

```dotenv
ESIGN_PROVIDER=documenso
DOCUMENSO_API_BASE_URL=https://sign.keeperfinancial.ca/api/v2
DOCUMENSO_PUBLIC_BASE_URL=https://sign.keeperfinancial.ca
DOCUMENSO_API_TOKEN=<api token>
DOCUMENSO_ICA_TEMPLATE_ID=<template id>
DOCUMENSO_ICA_SIGNER_RECIPIENT_ID=<recipient id>
```

Recreate the Keeper API after changing these, and confirm the production config validator
passes (it requires the exact HTTPS `/api/v2` + `sign.keeperfinancial.ca` shapes).

## 6. Backup

- Documenso Postgres (`documenso-db` volume), `documenso-uploads`, and the
  `certificates/cert.p12` + passphrase — all backed up on the same schedule as Keeper
  (`docs/operations/backup-restore-runbook.md`). The signing cert/passphrase is a separate
  crown-jewel offline copy.

## 7. End-to-end verification (day-one gate)

1. Sign in to Documenso as admin; confirm the ICA template + recipient resolve.
2. From Keeper, exercise the onboarding e-sign flow: create a synthetic onboarding
   assignment → issue the envelope → open the signing link → sign → refresh provider status
   → confirm `COMPLETED` satisfies the exact assignment only.
3. Confirm a `DRAFT`/ambiguous/unavailable provider response fails closed (readiness stays
   unsatisfied) and a rejected envelope is replaceable with predecessor history preserved.

## 8. Stop conditions

Stop before exposing `sign.keeperfinancial.ca` if: any default secret remains; images are
unpinned; SMTP is still Mailpit (capture-only); the signing cert/passphrase has no offline
backup; `nginx -t` fails; the Keeper production validator rejects the `DOCUMENSO_*` shape;
the host CPU cannot execute the image's native addons (§1.1); or the e-sign ceremony cannot
complete end-to-end.
