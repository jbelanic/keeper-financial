# Keeper Financial side-by-side deployment and cutover runbook

- **Status:** owner-approved deployment execution runbook for target Ubuntu host `inspiron`
- **Owner deploy approval:** 2026-07-30
- **Purpose:** run and validate the Keeper stack beside the existing WordPress production site before any DNS or public-port cutover

This runbook separates safe side-by-side validation from the final host-managed Nginx cutover. It preserves the repository boundary: local Docker Compose services, owner-hosted Supabase for production identity (decision 46; dev/test uses the local Supabase CLI/Auth stack), private MinIO, fail-closed ClamAV, and no public exposure of internal service ports.

For the from-scratch, command-by-command Ubuntu installation checklist, use
`docs/DEPLOYMENT_INSPIRON_STEP_BY_STEP.md`. This document remains the shorter
architecture, security-boundary, environment-mode, and cutover reference.

## 1. Confirmed deployment modes

### 1.1 Side-by-side validation mode

Use this before replacing WordPress.

- WordPress keeps public `80/443`.
- Keeper binds only loopback ports:
  - web: `127.0.0.1:3000`
  - API: `127.0.0.1:8000`
  - PostgreSQL: `127.0.0.1:5432`
  - MinIO: `127.0.0.1:9000` and `127.0.0.1:9001`
  - ClamAV: `127.0.0.1:3310`
  - No local Supabase CLI stack runs on the target host; production identity is owner-hosted Supabase (decision 46). A local CLI stack is used only for dev/test on a separate workstation or dev host.
- The default Compose file does **not** start the Documenso TLS bridge and does not bind loopback `443`.
- Test from the host shell or through SSH tunnels. Do not publish temporary internal ports.

### 1.2 Final public cutover mode

Use this only after side-by-side validation passes and the existing WordPress site is backed up.

- Retain the existing host-managed Nginx/Let's Encrypt service that owns public `80/443`.
- Install/load the reviewed Keeper server-block template from `infrastructure/nginx/keeper-financial.conf`, adapted only to the host's established certificate and ACME include conventions.
- Nginx is the only public ingress on `80/443`.
- Nginx proxies public web traffic to `127.0.0.1:3000` and same-origin API traffic to `127.0.0.1:8000` without stripping the `/api/` prefix.
- Internal service ports remain loopback/firewall-protected.

## 2. Supabase boundary

Production identity uses the owner-hosted Supabase project (decision 46) because the target host cannot run the local Supabase CLI container stack (SIGILL/exit 132). The repository-tracked local Supabase CLI/Auth stack (`supabase/config.toml`) is retained for dev/test only and is not started on the target host.

Required facts:

- The API accepts exactly two identity shapes and fails closed otherwise: the exact local CLI endpoint (issuer `http://127.0.0.1:54321/auth/v1`, JWKS/user via `host.docker.internal`), or an exact HTTPS `.supabase.co` endpoint whose host matches `NEXT_PUBLIC_SUPABASE_URL` (issuer `/auth/v1`, JWKS `/auth/v1/.well-known/jwks.json`, user `/auth/v1/user`, default/`443` port).
- `SUPABASE_ISSUER`, `SUPABASE_JWKS_URL`, and `SUPABASE_USER_URL` derive from the hosted project base URL (`NEXT_PUBLIC_SUPABASE_URL`).
- The hosted project keeps Supabase Storage and its S3 protocol disabled.
- Supabase Auth proves identity only; application PostgreSQL relationships/roles/lifecycle still authorize access.
- Only the hosted project's browser-safe anon key may be copied into `NEXT_PUBLIC_SUPABASE_ANON_KEY` and `SUPABASE_ANON_KEY`.
- Never copy the service-role key, secret key, signing key, JWT secret, confirmation links, access tokens, or refresh tokens into `.env`, Git, shell history, screenshots, or evidence.
- ES256 asymmetric JWKS only; never enable HS256 or `none`.

## 3. Pre-cutover `.env` values

Start from `.env.example` and replace every `change-me` value. For side-by-side host/SSH-tunnel validation, keep public browser URLs local:

```dotenv
APP_ENV=production
DEBUG=false
DEV_AUTH_ENABLED=false
REQUIRE_ADMIN_MFA=true

WEB_ORIGIN=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://apply.localhost:3000,http://127.0.0.1:8000

NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SUPABASE_URL=https://hdzmlwhubkecegrhptdd.supabase.co
SUPABASE_ISSUER=https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1
SUPABASE_JWKS_URL=https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_USER_URL=https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1/user
NEXT_PUBLIC_MORTGAGE_APPLICATION_URL=http://apply.localhost:3000/

MORTGAGE_APPLICATION_PROVIDER=keeper_secure_application
MORTGAGE_APPLICATION_URL=http://apply.localhost:3000/
MORTGAGE_APPLICATION_ALLOWED_HOSTS=apply.localhost

BORROWER_APPLICATION_ENABLED=true
BORROWER_REAL_DATA_ENABLED=false
# Browser-facing origin of the mortgage-application web app. It is used to build
# agent referral links, so it must be the application host the browser visits —
# `apply.localhost:3000` — and not the API at :8000, which has no application page.
# The local origin guard is unaffected: apps/web/proxy.ts rewrites Host/Origin to
# localhost:8000 / http://localhost:8000 for proxied /api/v1 requests.
BORROWER_APPLICATION_ORIGIN=http://apply.localhost:3000
```

Keep `BORROWER_REAL_DATA_ENABLED=false` until the deployed runtime evidence is complete and the consent catalog marker is deliberately set for the exact approved version/digest.

## 4. Final cutover `.env` values

For public cutover, rebuild the web image after changing `NEXT_PUBLIC_*` values because Next.js embeds them at build time:

```dotenv
APP_ENV=production
DEBUG=false
DEV_AUTH_ENABLED=false
REQUIRE_ADMIN_MFA=true

WEB_ORIGIN=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://apply.localhost:3000,http://127.0.0.1:8000

NEXT_PUBLIC_SITE_URL=https://keeperfinancial.ca
NEXT_PUBLIC_API_BASE_URL=https://keeperfinancial.ca
NEXT_PUBLIC_SUPABASE_URL=https://hdzmlwhubkecegrhptdd.supabase.co
SUPABASE_ISSUER=https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1
SUPABASE_JWKS_URL=https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_USER_URL=https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1/user
NEXT_PUBLIC_MORTGAGE_APPLICATION_URL=https://apply.keeperfinancial.ca/

MORTGAGE_APPLICATION_PROVIDER=keeper_secure_application
MORTGAGE_APPLICATION_URL=https://apply.keeperfinancial.ca/
MORTGAGE_APPLICATION_ALLOWED_HOSTS=apply.keeperfinancial.ca

BORROWER_APPLICATION_ENABLED=true
BORROWER_REAL_DATA_ENABLED=false
BORROWER_APPLICATION_ORIGIN=https://apply.keeperfinancial.ca
```

Notes:

- `NEXT_PUBLIC_API_BASE_URL=https://keeperfinancial.ca` makes public browser API calls same-origin through Nginx rather than to the user's own `localhost`.
- The API production validator intentionally keeps `WEB_ORIGIN`/`CORS_ORIGINS` loopback because Nginx is the trusted public ingress and server-side browser-facing borrower requests are same-origin.
- `NEXT_PUBLIC_SUPABASE_URL` is the owner-hosted Supabase project base (`https://hdzmlwhubkecegrhptdd.supabase.co`) per decision 46, so remote candidate/admin Auth no longer needs a local-Supabase proxy. The API still fails closed unless the issuer/JWKS/user are the exact hosted `.supabase.co` endpoints on that same host.

## 5. Side-by-side startup

From the repository root on the target host:

```bash
cp .env.example .env
${EDITOR:-vi} .env
```

The target host runs no local Supabase CLI stack (decision 46). Set the hosted project's
`NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_ISSUER`, `SUPABASE_JWKS_URL`, and
`SUPABASE_USER_URL` in `.env` and copy only its browser-safe anon key. Then generate
borrower key files outside Git if they do not already exist:

```bash
mkdir -p secrets
chmod 700 secrets
python3 - <<'PY'
import base64, json, os
path = 'secrets/borrower_encryption_keyring'
if not os.path.exists(path):
    data = {'version': 1, 'keys': {'001': base64.b64encode(os.urandom(32)).decode('ascii')}}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
        f.write('\n')
PY
python3 - <<'PY'
import os
path = 'secrets/borrower_capability_hmac_key'
if not os.path.exists(path):
    with open(path, 'wb') as f:
        f.write(os.urandom(32))
PY
chmod 400 secrets/borrower_encryption_keyring secrets/borrower_capability_hmac_key
```

Render and start the side-by-side stack:

```bash
docker compose config --quiet
docker compose up -d db minio minio-init clamav
docker compose run --rm --build api alembic upgrade head
docker compose run --rm --build api alembic current --check-heads
docker compose run --rm --build api alembic check
docker compose up --build -d api web
```

Validate locally:

```bash
docker compose ps --all
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/health/db
curl --fail http://127.0.0.1:9000/minio/health/live
curl --fail http://127.0.0.1:3000/
curl --fail "https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1/.well-known/jwks.json" >/dev/null
curl --fail "https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1/health" >/dev/null
```

For workstation browser validation without exposing ports, use SSH tunnels:

```bash
ssh \
  -L 3000:127.0.0.1:3000 \
  -L 8000:127.0.0.1:8000 \
  user@inspiron
```

Then browse locally to `http://localhost:3000` and `http://apply.localhost:3000`.

## 6. Optional Documenso TLS bridge

The default side-by-side stack intentionally does not bind `127.0.0.1:443`. If an approved Documenso ceremony is needed, first confirm the external `documenso_default` Docker network exists and WordPress or another web server is not already using loopback `443` in a conflicting way. Then run the opt-in compose overlay:

```bash
./infrastructure/documenso/generate-local-tls.sh
docker compose -f compose.yaml -f compose.documenso.yaml config --quiet
docker compose -f compose.yaml -f compose.documenso.yaml up -d documenso-tls api
```

Do not enable this overlay merely to make the API start; the base API no longer depends on the Documenso TLS bridge while `ESIGN_PROVIDER=disabled`. This overlay and its self-signed loopback `443` bridge are **local-dev only**; production serves Documenso at `sign.keeperfinancial.ca` through the host Nginx with a real certificate, never through `compose.documenso.yaml`.

## 7. Nginx cutover

Do not perform this step until WordPress files/database are backed up and side-by-side validation has passed.

Back up the host's existing Nginx configuration. Copy the reviewed Keeper template into the host's established `sites-available`/include layout, adapting certificate paths and ACME challenge handling only to match the existing working WordPress/Certbot convention. Do not replace the global Nginx configuration or alter unrelated virtual hosts.

```bash
sudo cp -a /etc/nginx /root/keeper-cutover-backup/nginx-before-keeper
sudo install -m 0644 infrastructure/nginx/keeper-financial.conf /etc/nginx/sites-available/keeper-financial.conf
sudo ln -s /etc/nginx/sites-available/keeper-financial.conf /etc/nginx/sites-enabled/keeper-financial.conf
sudo nginx -t
```

Reload Nginx only after `nginx -t` succeeds. A reload preserves existing working WordPress/Immich virtual hosts; do not stop Nginx or start Caddy:

```bash
sudo systemctl reload nginx
```

Verify only Nginx owns public `80/443` and internal Keeper services remain loopback:

```bash
sudo ss -ltnp | grep -E ':(80|443|3000|8000|5432|9000|9001|3310)\b'
curl -I https://keeperfinancial.ca/
curl -I https://www.keeperfinancial.ca/
curl -I https://apply.keeperfinancial.ca/
curl --fail https://keeperfinancial.ca/api/v1/recruitment/postings?limit=1
```

Negative probes from an external network should fail for every internal port except public `80/443`.

## 8. Stop conditions

Stop deployment or cutover if:

- any internal service is externally reachable outside Nginx `80/443`;
- WordPress backup is missing before cutover;
- Nginx/Let's Encrypt TLS fails for `keeperfinancial.ca` or `apply.keeperfinancial.ca`;
- `docker compose config --quiet`, Alembic head/check, API health, DB health, MinIO health, or ClamAV verification fails;
- Supabase Storage or its S3 protocol is enabled;
- identity is not one of the two approved shapes (the exact local CLI endpoint, or the exact hosted `.supabase.co` host matching `NEXT_PUBLIC_SUPABASE_URL`), or Cloudflare R2 or another unapproved hosted replacement appears;
- public browser API calls still target `localhost` after final cutover env values are set;
- tokens, secrets, capability values, key material, document contents, SIN, or raw borrower payloads appear in logs/evidence;
- real-data submission is enabled without deployed runtime evidence and the consent-catalog `real_data_approved=true` marker.
