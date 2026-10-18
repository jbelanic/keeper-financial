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


## 3. Public URLs and DNS/TLS

- Real DNS: `sign.keeperfinancial.ca` → `inspiron`.
- Set the Documenso public URLs to the production origin and recreate the app:

```dotenv
NEXTAUTH_URL=https://sign.keeperfinancial.ca
NEXT_PUBLIC_URL=https://sign.keeperfinancial.ca
NEXT_PUBLIC_API_URL=https://sign.keeperfinancial.ca
NEXT_PUBLIC_WEBAPP_URL=https://sign.keeperfinancial.ca
NEXT_PRIVATE_INTERNAL_WEBAPP_URL=https://sign.keeperfinancial.ca
```

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
or the e-sign ceremony cannot complete end-to-end.
