# Deploy Keeper Financial on `inspiron`: step-by-step implementation guide

- **Target:** Ubuntu 24.04 LTS host `inspiron`
- **Deployment model:** Keeper beside the existing WordPress and Immich services, followed by a controlled Nginx cutover
- **Repository branch to deploy:** `main` only
- **Companion policy/runbook:** `docs/DEPLOYMENT_SIDE_BY_SIDE.md`
- **Public ingress:** the host's existing Nginx and Let's Encrypt installation
- **Status:** executable installation checklist; it does not waive the stop conditions and unresolved production decisions below

This is the command-by-command guide. `DEPLOYMENT_SIDE_BY_SIDE.md` remains the shorter architecture, security-boundary, and cutover runbook.

> **Repository path:** the authoritative Markdown files are in `docs/`, not `docx/`. If `docx/` is an exported handoff folder, refresh it from the merged `main` branch before using it. Do not treat an older exported copy as authoritative.

## 0. Read this before running commands

### 0.1 Command labels

Every command is labelled by who runs it:

- **`[SON/ROOT]`** — the server administrator, using a single account with `sudo` (there is no separate restricted deploy account).
- **`[WORKSTATION]`** — the owner's or administrator's separate computer.
- **`[CUTOVER]`** — public-impacting command; run only in the agreed cutover window.
- **`[ROLLBACK]`** — run only to reverse a failed cutover.

Docker daemon access is root-equivalent. In this guide, the single `sudo` administrator runs Git, Docker, and system operations.

### 0.2 What this guide can deploy now

The merged source can be installed, migrated, and smoke-tested side by side without touching WordPress. It can then serve the public site and accountless borrower application through Nginx with `BORROWER_REAL_DATA_ENABLED=false`.

The following are **not solved by installation commands** and must not be guessed:

1. **Public candidate/administrator authentication:** production identity uses the owner-hosted Supabase project (decision 46) and the API validates the exact hosted `.supabase.co` shape. Remote candidate/admin sign-in still requires the hosted project's URL/key and email/redirect configuration plus genuine remote-browser evidence before it is claimed ready.
2. **First production administrator:** `seed_local.py` and `link_local_admin_identity.py` are deliberately local/synthetic-only. Use the production bootstrap command instead: `scripts/bootstrap_admin_identity.py` (requires `APP_ENV=production`) with the exact hosted-Supabase subject UUID, verified email, and display name. It never links by email alone, never uses service-role credentials, and never overwrites a genuine provider subject.
3. **Real borrower data:** keep `BORROWER_REAL_DATA_ENABLED=false`. Real submission requires `BORROWER_APPLICATION_ENABLED=true` + `BORROWER_REAL_DATA_ENABLED=true` **and** the active consent-catalog `real_data_approved=true` marker, which is set via `scripts/approve_consent_real_data.py` (`APP_ENV=production`) with the exact approved version/digest — plus deployed evidence.
4. **Transactional email:** SMTP2GO is the approved production provider (PR #44). Configure `SMTP_HOST`/`SMTP_PORT`/`SMTP_USE_TLS`/`SMTP_USERNAME`/`SMTP_PASSWORD`/`SMTP_FROM` in `.env`; Mailpit is local-capture only and is not production delivery.
5. **E-sign and Documenso:** Documenso is **not deployable on this host**. Its image loads native addons (`@img/sharp-linuxmusl-x64`, `@napi-rs/canvas-linux-x64-musl`) that require SSE4.1/SSE4.2/AVX; this CPU (AMD Athlon II X4 630) lacks all three and the container dies with `Illegal instruction (core dumped)` / exit 132 on start. No Compose or environment change fixes that — see the CPU baseline and stop conditions in `docs/operations/documenso-deployment.md`. Consequently Keeper runs with **`ESIGN_PROVIDER=manual`**: the contractor agreement is sent, signed, and retained entirely outside Keeper, and an administrator records the executed-agreements attestation (`external_esign_provider` or `signed_copy_on_file` plus a reference and verified date) before onboarding can complete. `disabled` behaves the same way and remains the safe default if unset. Provider mode (`ESIGN_PROVIDER=documenso` + `DOCUMENSO_*`) stays available in code for a future host that supports the required instruction set; do not attempt it here. Do **not** start `compose.documenso.yaml` anywhere — it is a local-dev TLS bridge whose loopback `443` bind conflicts with host Nginx.
6. **Production acceptance:** source tests and a successful deployment do not prove backup/restore, monitoring, incident response, privacy/legal review, or full operational readiness.

If the intended launch requires candidate/admin login on day one, stop before public cutover and close items 1 and 2 through reviewed source changes.

### 0.3 Destructive commands prohibited by this guide

Do not run any of these during installation or routine rollback:

```text
docker compose down --volumes
docker volume rm ...
docker system prune --volumes
npx supabase stop --no-backup
git reset --hard
git clean -fd
```

Do not stop, recreate, rename, or prune unrelated WordPress, Immich, database, proxy, or Docker resources.

## 1. Understand the deployment boundary

### 1.1 Outside Docker

| Component | Responsibility |
| --- | --- |
| Ubuntu | Host OS, filesystem, users, SSH, firewall, clock, swap, updates |
| Nginx | Only public listener on `80/443`; keeps unrelated virtual hosts intact |
| Certbot/Let's Encrypt | Existing certificate issuance and renewal |
| Git | Fetches merged source from GitHub |
| Node.js/npm | Dev/test only: launches the pinned Supabase CLI through `npx` (no Supabase CLI runs on the target host; decision 46) |
| DNS | `keeperfinancial.ca`, `www`, and `apply` records |
| Backup storage | WordPress, Nginx, Keeper PostgreSQL, MinIO, Auth, and key backups |

### 1.2 Docker Compose services in `compose.yaml`

| Service | Host binding | Purpose |
| --- | --- | --- |
| `db` | `127.0.0.1:5432` | Keeper application PostgreSQL |
| `minio` | `127.0.0.1:9000`, `127.0.0.1:9001` | Private object storage and local console |
| `minio-init` | none | Idempotently creates a private bucket |
| `clamav` | `127.0.0.1:3310` | Fail-closed malware scanning |
| `api` | `127.0.0.1:8000` | FastAPI application and migrations |
| `web` | `127.0.0.1:3000` | Next.js standalone server |

The `keeper_postgres`, `keeper_minio`, and `keeper_clamav` named volumes hold durable state. Do not delete them.

### 1.3 Supabase identity services

The target host runs **no** local Supabase CLI stack (decision 46). Production identity
uses the owner-hosted Supabase project (`https://hdzmlwhubkecegrhptdd.supabase.co`,
region `us-east-2`, ES256 asymmetric JWKS), configured through `NEXT_PUBLIC_SUPABASE_URL`
and the derived `SUPABASE_ISSUER`/`SUPABASE_JWKS_URL`/`SUPABASE_USER_URL`. The
repository-tracked `supabase/config.toml` remains for dev/test only and is not started here.

The API accepts only the exact hosted `.supabase.co` shape (same host as
`NEXT_PUBLIC_SUPABASE_URL`, exact `/auth/v1` paths, default/`443` port) or the exact local
CLI shape, and fails closed otherwise. The hosted project keeps Supabase Storage and its
S3 protocol disabled. No local Supabase, Studio, Mailpit, or Supabase database port exists
on this host, so there is nothing here to expose or firewall.

## 2. Phase A — host inspection and go/no-go

Run this before installing or changing anything.

### 2.1 Record the host and capacity

**`[SON/ROOT]`**

```bash
hostnamectl
lsb_release -a
uname -m
free -h
swapon --show
df -h /
df -h /var/lib/docker 2>/dev/null || true
uptime
```

Required interpretation:

- architecture must be `x86_64`/`amd64`;
- keep at least **20–40 GB free** for initial installation; more is preferable for images and backups;
- on this 11.4 GB host, configure **4–8 GB swap** if adequate swap is absent;
- stop if the existing WordPress/Immich load already leaves insufficient memory or disk headroom.

Do not create swap blindly. If swap is absent and at least 10 GB disk remains after reserving application/backup space, an 8 GB swapfile can be added:

**`[SON/ROOT]`**

```bash
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
swapon --show
```

### 2.2 Inventory existing listeners and services

**`[SON/ROOT]`**

```bash
sudo ss -ltnp
sudo systemctl --no-pager --full status nginx
sudo nginx -t
sudo certbot certificates
sudo systemctl list-timers --all | grep -E 'certbot|nginx' || true
sudo docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}' 2>/dev/null || true
```

Expected before Keeper starts:

- Nginx owns public `80/443`;
- WordPress and Immich continue to run;
- Keeper ports `3000`, `8000`, `5432`, `9000`, `9001`, and `3310` are unused; no local Supabase CLI ports (`54320`–`54324`) are needed on this host because production identity is hosted (decision 46).

If any intended Keeper port is occupied, stop. Do not stop its owner. Record the conflict and make a reviewed port-binding change instead.

### 2.3 Preserve sanitized Nginx evidence

Do not paste the full Nginx configuration into chat or email. Store a root-only copy on the host:

**`[SON/ROOT]`**

```bash
sudo install -d -m 0700 /root/keeper-preflight
sudo sh -c 'nginx -T > /root/keeper-preflight/nginx-T-before.txt 2>&1'
sudo sh -c 'ss -ltnp > /root/keeper-preflight/listeners-before.txt'
sudo sh -c 'certbot certificates > /root/keeper-preflight/certificates-before.txt 2>&1'
```

Identify which enabled-site symlink currently serves each Keeper hostname:

**`[SON/ROOT]`**

```bash
sudo ls -l /etc/nginx/sites-enabled
sudo grep -R --line-number --fixed-strings 'server_name keeperfinancial.ca' /etc/nginx/sites-available /etc/nginx/conf.d 2>/dev/null
sudo grep -R --line-number --fixed-strings 'server_name apply.keeperfinancial.ca' /etc/nginx/sites-available /etc/nginx/conf.d 2>/dev/null
```

Stop if WordPress and Immich share one indivisible server configuration that cannot be switched without affecting Immich.

## 3. Phase B — back up the current public service

Do this before any Nginx, certificate, or cutover change.

### 3.1 Back up Nginx and certificate metadata

**`[SON/ROOT]`**

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
sudo install -d -m 0700 "/var/backups/keeper-cutover/$STAMP"
printf '%s\n' "$STAMP" | sudo tee /root/keeper-preflight/backup-stamp >/dev/null
sudo tar -C /etc -czf "/var/backups/keeper-cutover/$STAMP/nginx-etc.tar.gz" nginx
sudo cp -a /etc/letsencrypt/renewal "/var/backups/keeper-cutover/$STAMP/letsencrypt-renewal"
sudo tar -tzf "/var/backups/keeper-cutover/$STAMP/nginx-etc.tar.gz" >/dev/null
```

This intentionally does not copy private certificate keys into the project or handoff documents. Preserve the host's established certificate backup procedure separately.

### 3.2 Back up WordPress files

Set `WORDPRESS_ROOT` to the exact root found in the active Nginx site. Do not print or copy `wp-config.php` contents.

**`[SON/ROOT]`**

```bash
STAMP="$(sudo cat /root/keeper-preflight/backup-stamp)"
WORDPRESS_ROOT=/replace/with/exact/wordpress/root
sudo test -f "$WORDPRESS_ROOT/wp-config.php"
sudo tar --one-file-system -C "$WORDPRESS_ROOT" -czf "/var/backups/keeper-cutover/$STAMP/wordpress-files.tar.gz" .
sudo tar -tzf "/var/backups/keeper-cutover/$STAMP/wordpress-files.tar.gz" >/dev/null
```

### 3.3 Back up the WordPress database

Use the host's existing tested database-backup process. If WP-CLI is already installed and working, it can read `wp-config.php` without displaying credentials:

**`[SON/ROOT]`**

```bash
STAMP="$(sudo cat /root/keeper-preflight/backup-stamp)"
WORDPRESS_ROOT=/replace/with/exact/wordpress/root
sudo wp --allow-root --path="$WORDPRESS_ROOT" db check
sudo wp --allow-root --path="$WORDPRESS_ROOT" db export "/var/backups/keeper-cutover/$STAMP/wordpress-database.sql"
sudo test -s "/var/backups/keeper-cutover/$STAMP/wordpress-database.sql"
```

If WP-CLI is unavailable, stop and use the son's existing WordPress database-backup procedure. Do not copy credentials from `wp-config.php` into shell history or this guide.

Create a root-only integrity manifest:

**`[SON/ROOT]`**

```bash
STAMP="$(sudo cat /root/keeper-preflight/backup-stamp)"
sudo sh -c "cd '/var/backups/keeper-cutover/$STAMP' && sha256sum nginx-etc.tar.gz wordpress-files.tar.gz wordpress-database.sql > SHA256SUMS"
sudo sh -c "cd '/var/backups/keeper-cutover/$STAMP' && sha256sum --check SHA256SUMS"
```

Do not continue to cutover unless these backups are non-empty and a restore owner/location is known.

## 4. Phase C — install missing host prerequisites

### 4.1 Base packages

**`[SON/ROOT]`**

```bash
sudo apt update
sudo apt install -y ca-certificates curl git gnupg jq openssl python3 rsync
```

Nginx and Certbot are already operational on `inspiron`; do not replace or reinstall them during this deployment.

### 4.2 Docker Engine and Compose

First check the existing installation:

**`[SON/ROOT]`**

```bash
sudo docker version
sudo docker compose version
sudo systemctl is-active docker
```

If all three succeed, keep the existing Docker installation. Do not remove or reinstall it because Immich or another service may depend on it.

Only on a host where Docker is genuinely absent, install from Docker's official Ubuntu repository:

**`[SON/ROOT]`**

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker run --rm hello-world
sudo docker compose version
```

Docker-published ports can bypass ordinary UFW assumptions. Keeper's tracked ports are bound to `127.0.0.1`, but the son must still inspect the effective `iptables`/`DOCKER-USER` policy and perform external negative probes before cutover.

### 4.3 Node.js 22 (dev/test only — not required on the target host)

The target host no longer runs the Supabase CLI (decision 46): production identity is owner-hosted, and the web application builds inside the tracked Node 22 Docker image. No host Node/npm install is required for the Keeper deployment itself.

Node.js 22 with the pinned Supabase CLI is needed only on a **dev/test workstation** that runs the local Supabase CLI stack. If such a workstation lacks Node 22, first confirm that no other workload depends on the installed host Node version, then install from the NodeSource APT repository:

**`[WORKSTATION]`**

```bash
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/nodesource.gpg >/dev/null
echo 'deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main' | sudo tee /etc/apt/sources.list.d/nodesource.list >/dev/null
sudo apt update
sudo apt install -y nodejs
node --version
npm --version
npx --yes supabase@2.109.1 --version
```

Expected: Node `v22.x` and Supabase CLI `2.109.1`.

## 5. Phase D — clone `main`

### 5.1 Deployment directory

The deployment lives at `/home/inspiron/keeper-financial`, owned by the single
`sudo` administrator account. No separate restricted account is created.

### 5.2 Clone the exact branch

GitHub's repository default branch may not be `main`, so the branch must be explicit.

**`[SON/ROOT]`**

```bash
git clone --branch main --single-branch https://github.com/jbelanic/keeper-financial.git /home/inspiron/keeper-financial
```

If the directory already contains a checkout, do not clone over it. Update it safely instead:

**`[SON/ROOT]`**

```bash
git -C /home/inspiron/keeper-financial status --short --branch
git -C /home/inspiron/keeper-financial fetch origin --prune
git -C /home/inspiron/keeper-financial switch main
git -C /home/inspiron/keeper-financial pull --ff-only origin main
```

Verify:

**`[SON/ROOT]`**

```bash
git -C /home/inspiron/keeper-financial status --short --branch
git -C /home/inspiron/keeper-financial rev-parse HEAD
git -C /home/inspiron/keeper-financial rev-parse origin/main
```

The two revisions must match and status must show only:

```text
## main...origin/main
```

Record the revision in the deployment evidence. Do not deploy an unmerged feature branch.

## 6. Phase E — create `.env` without exposing values

### 6.1 Install a root-only environment file

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
sudo install -o root -g root -m 0600 .env.example .env
git check-ignore .env
sudoedit .env
```

`git check-ignore` must report `.env`. Replace every `change-me` value with a unique generated value. Use a password manager; do not paste values into chat, tickets, screenshots, or Git.

Generate database and MinIO values independently. Prefer at least 32 random characters using the password manager. Keep `POSTGRES_PASSWORD` URL-safe because Compose constructs `DATABASE_URL` from it.

Check for unresolved placeholders without printing values:

**`[SON/ROOT]`**

```bash
sudo awk -F= '/^[A-Za-z_][A-Za-z0-9_]*=.*change-me/ {print "unresolved key: "$1; bad=1} END {exit bad}' .env
```

No output and exit code `0` means no `change-me` values remain.

### 6.2 Initial side-by-side values

Use these non-secret values for the first start:

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

BORROWER_APPLICATION_ENABLED=false
BORROWER_REAL_DATA_ENABLED=false
# Loopback-stage value only. While BORROWER_APPLICATION_ENABLED=false this variable
# is neither validated nor used to serve the application; production enablement
# requires exactly https://apply.keeperfinancial.ca (the configuration validator
# enforces it). When enabled locally, it is the browser-facing application host.
BORROWER_APPLICATION_ORIGIN=http://apply.localhost:3000
# No e-sign provider on this host (§0.2 item 5). Onboarding completes by
# administrator attestation of the externally signed contractor agreement.
ESIGN_PROVIDER=manual
```

`BORROWER_APPLICATION_ENABLED=false` is intentional during this production-mode loopback smoke test. Production borrower cryptography accepts only the exact HTTPS `apply.keeperfinancial.ca` origin, so do not combine production mode, borrower enablement, and a loopback borrower origin.

## 7. Phase F — configure hosted Supabase identity

Decision 46 moves production identity to the owner-hosted Supabase project. The target host runs **no** local Supabase CLI stack, generates **no** signing key, and starts **no** Supabase containers. The repository-tracked `supabase/config.toml` remains for dev/test and must keep `[storage].enabled = false` and `[storage.s3_protocol].enabled = false`.

### 7.1 Set the hosted identity values

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
sudoedit .env
```

Set (all non-secret except the anon key, which is browser-visible, not authorization):

```dotenv
NEXT_PUBLIC_SUPABASE_URL=https://hdzmlwhubkecegrhptdd.supabase.co
SUPABASE_ISSUER=https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1
SUPABASE_JWKS_URL=https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_USER_URL=https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1/user
SUPABASE_JWT_ALGORITHMS=ES256
```

Copy only the hosted project's browser-safe anon key into `SUPABASE_ANON_KEY` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Never copy the hosted service-role key, secret key, JWT secret, or signing key into `.env`, Git, shell history, screenshots, or evidence.

### 7.2 Validate the hosted identity boundary

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
curl --fail --silent --show-error https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1/.well-known/jwks.json >/dev/null
curl --fail --silent --show-error https://hdzmlwhubkecegrhptdd.supabase.co/auth/v1/health >/dev/null
sudo ss -ltnp | grep -E ':(54320|54321|54322|54323|54324)\b' || echo 'no local Supabase listeners (expected)'
grep -A4 '^\[storage\]' supabase/config.toml
grep -A2 '^\[storage.s3_protocol\]' supabase/config.toml
```

Both storage settings must remain `enabled = false` in the tracked config. No local Supabase Studio, Mailpit, or Supabase database runs on this host, so there is nothing to expose or firewall. The API fails closed at startup unless the identity endpoints are the exact hosted `.supabase.co` shape above (or the exact local CLI shape on a dev/test host).

## 8. Phase G — generate borrower key files

Generate keys even though borrower intake remains disabled during the first smoke test. Store an encrypted offline recovery copy before enabling borrower intake.

### 8.1 Generate once

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
sudo install -d -o root -g root -m 0700 secrets
sudo bash -c 'set -euo pipefail; python3 -c "
import base64, json, os
from pathlib import Path
root = Path(\"/home/inspiron/keeper-financial/secrets\")
keyring = root / \"borrower_encryption_keyring\"
hmac_key = root / \"borrower_capability_hmac_key\"
if keyring.exists() or hmac_key.exists():
    raise SystemExit(\"STOP: borrower key file already exists; do not overwrite or rotate during install\")
with keyring.open(\"x\", encoding=\"utf-8\") as stream:
    json.dump({\"version\": 1, \"keys\": {\"001\": base64.b64encode(os.urandom(32)).decode(\"ascii\")}}, stream)
    stream.write(chr(10))
with hmac_key.open(\"xb\") as stream:
    stream.write(os.urandom(32))
os.chmod(keyring, 0o400)
os.chmod(hmac_key, 0o400)
print(\"OK\")
"'
```

Do not run this block again. Overwriting the keyring can make existing borrower data permanently unreadable; replacing the HMAC key invalidates active capabilities.

### 8.2 Build the API, determine its container group, and grant read-only access

The API runs as a non-root `keeper` user. Grant only its numeric container group read access while retaining host root ownership.

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
sudo docker compose build api
API_GID="$(sudo docker compose run --rm --no-deps --entrypoint id api -g)"
case "$API_GID" in (*[!0-9]*|'') echo 'STOP: invalid API container GID' >&2; exit 1;; esac
sudo chown root:"$API_GID" secrets/borrower_encryption_keyring secrets/borrower_capability_hmac_key
sudo chmod 0440 secrets/borrower_encryption_keyring secrets/borrower_capability_hmac_key
sudo stat -c '%a %u:%g %n' secrets/borrower_encryption_keyring secrets/borrower_capability_hmac_key
```

Do not display file contents. Store an encrypted offline copy under the approved custody procedure. A database/MinIO backup without this keyring cannot restore borrower data.

## 9. Phase H — render configuration before startup

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
sudo docker compose config --quiet
sudo docker compose -f compose.yaml -f compose.documenso.yaml config --quiet
```

The second command validates syntax only. Do not start the Documenso overlay.

Confirm the effective host bindings without printing environment values:

**`[SON/ROOT]`**

```bash
sudo docker compose config --format json | jq -r '.services | to_entries[] | .key as $service | (.value.ports // [])[]? | [$service, .host_ip, (.published|tostring), (.target|tostring)] | @tsv'
```

Every published Keeper port must show host IP `127.0.0.1`. Stop if a value is blank, `0.0.0.0`, `::`, or a public interface.

## 10. Phase I — start infrastructure and migrate

### 10.1 Start PostgreSQL, MinIO, and ClamAV

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
sudo docker compose up -d db minio minio-init clamav
sudo docker compose ps --all
```

The first ClamAV startup can take several minutes while signatures initialize. Wait until `db`, `minio`, and `clamav` are healthy and `minio-init` exits successfully:

**`[SON/ROOT]`**

```bash
sudo docker compose ps --all
sudo docker compose logs --no-color --tail=100 clamav
```

Do not continue if ClamAV remains unhealthy or signature updates fail.

### 10.2 Apply and verify migrations

Migrations do not run automatically. Back up retained data before every future migration.

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
sudo docker compose run --rm --build api alembic upgrade head
sudo docker compose run --rm api alembic current --check-heads
sudo docker compose run --rm api alembic check
```

All three commands must succeed. `current --check-heads` and `alembic check` prove different things; do not omit either.

### 10.3 Start API and web

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
sudo docker compose up --build -d api web
sudo docker compose ps --all
```

All long-running services must be `Up` and healthy. `minio-init` should be exited with status `0`.

## 11. Phase J — side-by-side smoke test

### 11.1 Host-shell probes

**`[SON/ROOT]`**

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/health >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8000/health/db >/dev/null
curl --fail --silent --show-error http://127.0.0.1:9000/minio/health/live >/dev/null
curl --fail --silent --show-error http://127.0.0.1:3000/ >/dev/null
curl --fail --silent --show-error 'http://127.0.0.1:8000/api/v1/recruitment/postings?limit=1' >/dev/null
sudo docker compose run --rm api python scripts/verify_clamav.py --host clamav --port 3310
```

Expected ClamAV result:

```text
clean: OK
EICAR: FOUND
```

The standard antivirus marker exists only in process memory and must not be written to disk or MinIO.

### 11.2 Confirm WordPress and Immich were not disturbed

**`[SON/ROOT]`**

```bash
sudo nginx -t
sudo systemctl is-active nginx
sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
curl -I https://keeperfinancial.ca/
```

At this stage the public request must still reach the existing WordPress site.

### 11.3 Confirm no Keeper internal service became public

**`[SON/ROOT]`**

```bash
sudo ss -ltnp | grep -E ':(80|443|3000|8000|5432|9000|9001|3310)\b'
```

Only Nginx should listen publicly on `80/443`; every Keeper/Supabase listener must be loopback-only or otherwise blocked by the reviewed host firewall.

### 11.4 SSH tunnel from the workstation

**`[WORKSTATION]`**

```bash
ssh -N \
  -L 3000:127.0.0.1:3000 \
  -L 8000:127.0.0.1:8000 \
  server-user@inspiron
```

Open:

- `http://localhost:3000`
- `http://apply.localhost:3000`

Checklist:

- [ ] public pages render;
- [ ] navigation and contact form load without console/network errors;
- [ ] API requests target the SSH-tunneled loopback API, not an unrelated host;
- [ ] `apply.localhost` renders the borrower host journey but submission remains unavailable while borrower intake is disabled;
- [ ] no local Supabase/Studio/Mailpit runs on the target host; production identity is owner-hosted (decision 46);
- [ ] no secrets, tokens, borrower answers, SIN, object keys, or filenames appear in screenshots or evidence.

## 12. Phase K — reboot persistence test before cutover

Do not assume `restart: unless-stopped` covers every Supabase CLI-managed service. Schedule a maintenance reboot only after the son confirms unrelated workloads can be restarted safely.

**`[SON/ROOT]`**

```bash
sudo reboot
```

After reconnecting:

**`[SON/ROOT]`**

```bash
sudo systemctl is-active docker nginx
cd /home/inspiron/keeper-financial
sudo docker compose up -d
sudo docker compose ps --all
curl --fail --silent --show-error http://127.0.0.1:8000/health >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8000/health/db >/dev/null
curl --fail --silent --show-error http://127.0.0.1:3000/ >/dev/null
```

If manual intervention is required, record it as an operational gap. Do not claim unattended restart readiness until a reviewed service unit and reboot evidence exist.

## 13. Phase L — public cutover prerequisites

All boxes must be checked before changing public Nginx routing:

- [ ] side-by-side smoke tests passed at the exact merged revision;
- [ ] WordPress files, database, and Nginx backup passed integrity checks;
- [ ] existing Immich and unrelated services are healthy;
- [ ] DNS authority and rollback TTL are known;
- [ ] apex/`www` certificate is valid and its exact paths are known;
- [ ] `apply.keeperfinancial.ca` DNS points to this host and has a valid certificate;
- [ ] the WordPress site can be disabled without disabling Immich/unrelated virtual hosts;
- [ ] Nginx template was reviewed against the host's actual include and Certbot conventions;
- [ ] external negative port probes are arranged;
- [ ] borrower encryption/HMAC keys have an encrypted offline recovery copy;
- [ ] `BORROWER_REAL_DATA_ENABLED=false` remains set;
- [ ] hosted Supabase identity (decision 46) is configured and its exact issuer/JWKS/user endpoints are validated;
- [ ] a rollback operator is present.

## 14. Phase M — DNS and certificate preparation

### 14.1 DNS

Create/verify records through the existing DNS provider:

```text
keeperfinancial.ca        A/AAAA -> inspiron public address
www.keeperfinancial.ca    A/AAAA or CNAME -> approved existing target
apply.keeperfinancial.ca  A/AAAA -> inspiron public address
```

Do not publish an IPv6 `AAAA` record unless IPv6 reaches the same reviewed Nginx/firewall boundary.

**`[WORKSTATION]`**

```bash
dig +short keeperfinancial.ca A
dig +short www.keeperfinancial.ca A
dig +short apply.keeperfinancial.ca A
dig +short keeperfinancial.ca AAAA
dig +short apply.keeperfinancial.ca AAAA
```

### 14.2 Obtain/verify the `apply` certificate

First check whether an existing certificate already covers the exact name:

**`[SON/ROOT]`**

```bash
sudo certbot certificates
```

If it does not, use the host's established Certbot method. The safe webroot pattern is:

**`[SON/ROOT]`**

```bash
sudo install -d -o root -g www-data -m 0755 /var/www/certbot
```

Before issuing, the existing port-80 Nginx configuration must route `/.well-known/acme-challenge/` for `apply.keeperfinancial.ca` to `/var/www/certbot` while all other `apply` requests return `404`. Validate and reload that temporary, HTTP-only server block, then run:

**`[SON/ROOT]`**

```bash
sudoedit /etc/nginx/sites-available/keeper-apply-acme.conf
```

Install this exact temporary content:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name apply.keeperfinancial.ca;

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 404;
    }
}
```

Enable only the temporary file, validate, and reload:

**`[SON/ROOT]`**

```bash
sudo ln -s /etc/nginx/sites-available/keeper-apply-acme.conf /etc/nginx/sites-enabled/keeper-apply-acme.conf
sudo nginx -t
sudo systemctl reload nginx
```

Stop if another enabled exact-host `apply.keeperfinancial.ca` block already
exists; do not create duplicate `server_name` ownership.

**`[CUTOVER]`**

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo certbot certonly --webroot -w /var/www/certbot -d apply.keeperfinancial.ca
sudo certbot certificates
```

Do not continue unless the resulting certificate paths match or are deliberately adapted in `infrastructure/nginx/keeper-financial.conf`.

## 15. Phase N — set final public values and rebuild

Edit only through `sudoedit`; do not print `.env`.

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
sudoedit .env
```

Set:

```dotenv
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
# Manual attestation of the externally signed agreement; no provider on this host.
ESIGN_PROVIDER=manual
```

Important:

- `NEXT_PUBLIC_*` values are embedded at image build time; a restart alone is insufficient.
- `NEXT_PUBLIC_SUPABASE_URL` is the owner-hosted Supabase project base (decision 46); remote candidate/admin login uses the hosted Auth service. Confirm the hosted project's redirect/email settings before relying on it.
- Do not set public HTTPS values in `WEB_ORIGIN`/`CORS_ORIGINS`; the current production validator requires the approved local-host values and borrower traffic is same-origin through the Next/Nginx boundary.

Validate secrets and render without printing values:

**`[SON/ROOT]`**

```bash
sudo awk -F= '/^[A-Za-z_][A-Za-z0-9_]*=.*change-me/ {print "unresolved key: "$1; bad=1} END {exit bad}' .env
sudo docker compose config --quiet
```

Verify that the non-root API process can load the exact production borrower key configuration without displaying key material:

**`[SON/ROOT]`**

```bash
sudo docker compose run --rm --no-deps api python -c "from pathlib import Path; from keeper_api.services.borrower_crypto import load_borrower_crypto_state; load_borrower_crypto_state(Path('/run/secrets/borrower_encryption_keyring'), Path('/run/secrets/borrower_capability_hmac_key'), '001', 'https://apply.keeperfinancial.ca', production=True)"
```

Rebuild/recreate API and web:

**`[SON/ROOT]`**

```bash
sudo docker compose up --build -d api web
sudo docker compose ps --all
curl --fail --silent --show-error http://127.0.0.1:8000/health >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8000/health/db >/dev/null
curl --fail --silent --show-error http://127.0.0.1:3000/ >/dev/null
```

### 15.1 Provision the first production administrator

The first administrator is linked from an explicit hosted-Supabase identity with the
production bootstrap command (`scripts/bootstrap_admin_identity.py`, decision 49), never the
local `seed_local.py`/`link_local_admin_identity.py` scripts (those are local/synthetic-only).
The command links the exact Supabase subject UUID + verified email to a `brokerage_admin`
account, idempotently and audited; it never links by email alone, never uses service-role
credentials, and never overwrites a genuine provider subject.

1. In the hosted Supabase dashboard (`https://hdzmlwhubkecegrhptdd.supabase.co`),
   **Authentication → Users → Add user** (or **Invite user**) with the administrator's
   email and a strong password.
2. Copy that user's **UUID** (the `id` shown in the Auth users list).
3. Run the bootstrap command (it refuses to run unless `APP_ENV=production`):

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
sudo docker compose run --rm -e APP_ENV=production api python scripts/bootstrap_admin_identity.py \
  --email '<admin-email>' \
  --subject '<supabase-uuid>' \
  --name '<display name>'
```

4. After public cutover (Phase P), sign in at `https://keeperfinancial.ca/auth/sign-in` with
   those credentials. The `brokerage_admin` role is granted exactly once (idempotent); verify
   the admin console loads.

Stop if the command refuses to run: confirm `APP_ENV=production`, that the `.env` uses the
exact hosted `.supabase.co` identity values (Phase N), and that the subject UUID came from the
hosted project (not a local Supabase CLI identity).

## 16. Phase O — install and review the Nginx template

Do not overwrite the current WordPress file. Install Keeper under a separate name:

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
sudo install -o root -g root -m 0644 infrastructure/nginx/keeper-financial.conf /etc/nginx/sites-available/keeper-financial.conf
sudoedit /etc/nginx/sites-available/keeper-financial.conf
```

Review/adapt only:

- exact certificate paths;
- the existing ACME challenge include/root convention;
- any host-standard TLS include;
- Nginx-version `http2` syntax if the installed version requires it.

Preserve:

- exact hostnames;
- `127.0.0.1:3000` and `127.0.0.1:8000` upstreams;
- `/api/` prefix preservation (`proxy_pass http://127.0.0.1:8000` with no trailing slash);
- `26m` Keeper request limit;
- 300-second upload/scanning timeouts;
- no routes to PostgreSQL, MinIO, ClamAV, Studio, Mailpit, or consoles.

Do not enable it yet if the old WordPress site uses the same `server_name`; duplicate host blocks produce ambiguous routing.

## 17. Phase P — controlled Nginx cutover

Set the exact enabled WordPress symlink after inspecting `/etc/nginx/sites-enabled`. This must be a symlink dedicated to the Keeper hostnames, not a shared Immich configuration.

**`[SON/ROOT]`**

```bash
WORDPRESS_SITE_LINK=/etc/nginx/sites-enabled/replace-with-exact-wordpress-symlink
KEEPER_SITE_LINK=/etc/nginx/sites-enabled/keeper-financial.conf
sudo test -L "$WORDPRESS_SITE_LINK"
sudo test -f /etc/nginx/sites-available/keeper-financial.conf
sudo test ! -e "$KEEPER_SITE_LINK"
```

Atomically switch enabled-site symlinks, validate, and automatically restore the WordPress symlink if validation fails:

**`[CUTOVER]`**

```bash
WORDPRESS_SITE_LINK=/etc/nginx/sites-enabled/replace-with-exact-wordpress-symlink
KEEPER_SITE_LINK=/etc/nginx/sites-enabled/keeper-financial.conf
WORDPRESS_SITE_TARGET="$(readlink "$WORDPRESS_SITE_LINK")"
sudo unlink /etc/nginx/sites-enabled/keeper-apply-acme.conf 2>/dev/null || true
sudo unlink "$WORDPRESS_SITE_LINK"
sudo ln -s /etc/nginx/sites-available/keeper-financial.conf "$KEEPER_SITE_LINK"
if ! sudo nginx -t; then
  sudo unlink "$KEEPER_SITE_LINK"
  sudo ln -s "$WORDPRESS_SITE_TARGET" "$WORDPRESS_SITE_LINK"
  sudo nginx -t
  echo 'CUTOVER ABORTED: WordPress Nginx link restored' >&2
  exit 1
fi
sudo systemctl reload nginx
```

Use `reload`, not `restart`. Do not stop Nginx and do not start Caddy.

## 18. Phase Q — public smoke test

### 18.1 From the server

**`[SON/ROOT]`**

```bash
curl --fail --silent --show-error --head https://keeperfinancial.ca/ >/dev/null
curl --fail --silent --show-error --head https://www.keeperfinancial.ca/ >/dev/null
curl --fail --silent --show-error --head https://apply.keeperfinancial.ca/ >/dev/null
curl --fail --silent --show-error 'https://keeperfinancial.ca/api/v1/recruitment/postings?limit=1' >/dev/null
sudo nginx -t
sudo systemctl is-active nginx
sudo docker compose ps --all
```

### 18.2 From an external workstation/network

**`[WORKSTATION]`**

```bash
curl -I https://keeperfinancial.ca/
curl -I https://www.keeperfinancial.ca/
curl -I https://apply.keeperfinancial.ca/
curl --fail 'https://keeperfinancial.ca/api/v1/recruitment/postings?limit=1'
```

Browser checklist:

- [ ] apex loads over trusted HTTPS;
- [ ] `www` redirects to apex;
- [ ] `apply` loads the borrower journey over trusted HTTPS;
- [ ] no mixed-content or localhost API request appears;
- [ ] borrower start/save works only with synthetic data;
- [ ] refresh/recovery remains private and no-store;
- [ ] browser storage contains no answers or SIN;
- [ ] upload rejects unsafe files and accepts only a generated safe synthetic document;
- [ ] `BORROWER_REAL_DATA_ENABLED=false` blocks real-data release;
- [ ] contact flow behaves as expected;
- [ ] WordPress is no longer public but remains intact for rollback;
- [ ] Immich and unrelated services remain healthy.

### 18.3 External negative port probes

From a separate network, every port below must be closed/filtered except public `80/443`:

**`[WORKSTATION]`**

```bash
for port in 3000 8000 5432 9000 9001 3310; do
  nc -vz -w 3 inspiron-public-address "$port"
done
```

A successful connection to any listed internal port is a stop condition. Remove public exposure before continuing.

### 18.4 Logs without leaking data

**`[SON/ROOT]`**

```bash
sudo docker compose logs --no-color --since=15m api web clamav minio | less
sudo journalctl -u nginx --since '-15 minutes' --no-pager
```

Review locally. Do not upload raw logs. Stop and treat as an incident if they contain tokens, cookies, keys, private URLs, SIN, borrower payloads, document contents, or unexpected filenames.

### 18.5 Agent referral links

An onboarded agent's `/agent` console shows their application link. Eligibility,
the link shape, administrator rotation, the assigned-agent draft-view boundary,
and verification queries are in `docs/operations/agent-referral-links.md`. The
link is built from `BORROWER_APPLICATION_ORIGIN`, which must be
`https://apply.keeperfinancial.ca`; a link on the API origin has no application
page behind it.

## 19. Rollback

Rollback Nginx if any public smoke test fails or unrelated services are affected. This does not delete Keeper data.

**`[ROLLBACK]`**

```bash
WORDPRESS_SITE_LINK=/etc/nginx/sites-enabled/replace-with-exact-wordpress-symlink
WORDPRESS_SITE_TARGET=/etc/nginx/sites-available/replace-with-exact-wordpress-target
KEEPER_SITE_LINK=/etc/nginx/sites-enabled/keeper-financial.conf
sudo test -f "$WORDPRESS_SITE_TARGET"
sudo unlink "$KEEPER_SITE_LINK" 2>/dev/null || true
sudo ln -s "$WORDPRESS_SITE_TARGET" "$WORDPRESS_SITE_LINK"
sudo nginx -t
sudo systemctl reload nginx
curl -I https://keeperfinancial.ca/
```

If Keeper itself must be stopped after public routing is restored:

**`[ROLLBACK]`**

```bash
cd /home/inspiron/keeper-financial
sudo docker compose stop web api
```

Do not stop shared Docker, Nginx, WordPress, Immich, Supabase, PostgreSQL, MinIO, or ClamAV unless the rollback owner determines that is necessary. Do not delete volumes.

If Nginx files were damaged, restore `/etc/nginx` from the timestamped backup, run `nginx -t`, and reload. A restore is an administrator decision; do not overwrite newer unrelated Nginx changes blindly.

## 20. Ongoing Keeper backup, off-host copy, and restore

The complete operational procedures — daily automated backups, daily verified encrypted USB
off-host copy (two rotating drives), 30-day rolling retention, quarterly isolated restore
drills, and alerting — are in `docs/operations/backup-restore-runbook.md`; incident response
is in `docs/operations/incident-response.md`; and the step-by-step restore drill is in
`docs/operations/restore-drill.md`. Use those runbooks; this section is a pointer, not a
substitute.

Scripts (decision 49 P0): `scripts/backup_all.sh` (coordinated encrypted PostgreSQL +
MinIO backup), `scripts/backup_postgres.sh` (encrypted `pg_dump`), `scripts/backup_minio.py`
(boto3 MinIO mirror), `scripts/backup_usb.sh` (verified encrypted USB copy),
`scripts/monitor_health.sh` (health/ClamAV/backup/USB freshness), `scripts/send_alert.py`
(alert email), and `scripts/reconcile_restore_deletions.py` (restore-time deletion safety
gate). Backups need approved encryption, off-host storage, retention, and isolated restore
tests; a backup that has never been restored is unproven.

### 20.1 PostgreSQL

**`[SON/ROOT]`**

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
sudo install -d -m 0700 /var/backups/keeper-postgres
cd /home/inspiron/keeper-financial
sudo sh -c "docker compose exec -T db sh -c 'pg_dump --format=custom --no-owner --no-acl -U \"\$POSTGRES_USER\" \"\$POSTGRES_DB\"' > '/var/backups/keeper-postgres/keeper-$STAMP.dump'"
sudo test -s "/var/backups/keeper-postgres/keeper-$STAMP.dump"
```

Test restoration only into an isolated database/container, never over live data.

### 20.2 MinIO

Use `scripts/backup_minio.py` (boto3) via `scripts/backup_all.sh` — the earlier
`quay.io/minio/mc` image cannot run on the below-baseline target host (decision 47). See
`docs/operations/backup-restore-runbook.md` for the full procedure and the verified
encrypted USB off-host copy.

### 20.3 Keys and hosted Supabase Auth

- Keep encrypted offline copies of both borrower key files. Never store them beside unencrypted backups.
- Auth is owner-hosted Supabase (decision 46), so the Supabase Auth database is a vendor-side concern: confirm the hosted project's backup/PITR posture and record recovery ownership. No local Supabase database exists on this host to back up.
- Do not assume a local `supabase stop` is a backup (this host has no local Supabase stack).

No real data should be accepted until PostgreSQL, MinIO, hosted Auth, keys, and required host configuration have a successful isolated restore exercise.

## 21. Updating to a later merged release

Never pull over uncommitted server changes and never deploy an unmerged branch.

### 21.1 Pre-update

**`[SON/ROOT]`**

```bash
git -C /home/inspiron/keeper-financial status --short --branch
git -C /home/inspiron/keeper-financial fetch origin --prune
git -C /home/inspiron/keeper-financial log --oneline HEAD..origin/main
```

Stop if status is dirty. Preserve deliberate server-only files outside Git; `.env`, `secrets/`, and Supabase signing keys are ignored.

Create PostgreSQL/MinIO backups before migration. Then update:

**`[SON/ROOT]`**

```bash
git -C /home/inspiron/keeper-financial switch main
git -C /home/inspiron/keeper-financial pull --ff-only origin main
git -C /home/inspiron/keeper-financial status --short --branch
```

### 21.2 Render, migrate, rebuild, and verify

**`[SON/ROOT]`**

```bash
cd /home/inspiron/keeper-financial
sudo docker compose config --quiet
sudo docker compose run --rm --build api alembic upgrade head
sudo docker compose run --rm api alembic current --check-heads
sudo docker compose run --rm api alembic check
sudo docker compose up --build -d api web
sudo docker compose ps --all
git -C /home/inspiron/keeper-financial log --oneline -1
curl --max-time 10 --fail --silent --show-error http://127.0.0.1:8000/health >/dev/null
curl --max-time 10 --fail --silent --show-error http://127.0.0.1:8000/health/db >/dev/null
# This host cannot reach its own public IP: the router does not hairpin NAT, so a
# bare https://keeperfinancial.ca/ request hangs until interrupted. Resolve the
# name to loopback to exercise the real Nginx vhost and TLS path instead.
curl --max-time 10 --fail --silent --show-error \
  --resolve keeperfinancial.ca:443:127.0.0.1 https://keeperfinancial.ca/ >/dev/null
sudo docker compose logs --since=10m api | grep -iE "traceback|error" || echo "api log clean"
```

### 21.3 Environment-only changes

`env_file` values are applied when a container is **created**, so `docker compose
restart api` keeps the previous environment and the change silently does not take
effect. After editing `.env` (or whichever file `KEEPER_ENV_FILE` names) recreate
the affected service:

```bash
sudo docker compose up -d --force-recreate api
sudo docker compose exec -T api printenv | grep -oE "^(SMTP|LEAD|BORROWER|ESIGN)_[A-Z_]+" | sort
```

No image rebuild is needed for environment values. A rebuild is required only when
source, dependencies, or Next.js `NEXT_PUBLIC_*` values change, because those are
embedded into the web bundle at build time.

Alembic downgrade is not the default rollback. If a forward migration has written data, restore/downgrade decisions require the migration-specific runbook and database owner.

## 22. Responsibility boundary

A single `sudo` administrator performs every step; there is no separate deploy account.

| Activity | Son/server administrator (`sudo`) |
| --- | --- |
| Read/fetch merged public source | Yes |
| Modify Git history or force push | No under this guide |
| Read `.env` or borrower keys | Yes, only as custodian |
| Run Docker/Supabase containers | Yes |
| Run migrations | Yes, after backup |
| Change Nginx/Certbot/DNS/firewall | Yes, cutover window only |
| Access WordPress/Immich data | Yes, only as existing administrator |
| Review local logs/evidence | Yes; redact before sharing |
| Enable real borrower data | Only after separate release controls/approval |
| Provision production administrators | Yes — `scripts/bootstrap_admin_identity.py` (§15.1) |

## 23. Final acceptance checklist

### Side-by-side installation

- [ ] host capacity and swap reviewed;
- [ ] existing service/listener inventory stored root-only;
- [ ] WordPress/Nginx backups verified;
- [ ] Docker Engine/Compose versions verified (no host Node/Supabase CLI required on the target; decision 46);
- [ ] deployment runs as the single `sudo` administrator account (no separate restricted account);
- [ ] exact merged `main` revision recorded;
- [ ] `.env`, borrower keys, and signing key are ignored and root-restricted;
- [ ] Supabase Storage/S3 disabled;
- [ ] Compose render and loopback bindings verified;
- [ ] migrations reached one head and `alembic check` passed;
- [ ] PostgreSQL, MinIO, ClamAV, API, web, and hosted Supabase JWKS probes passed;
- [ ] clean and EICAR ClamAV verification passed;
- [ ] SSH-tunnel browser smoke passed;
- [ ] WordPress and Immich remained healthy.

### Public cutover

- [ ] hosted Supabase identity (decision 46) configured and validated; public Auth/admin-bootstrap boundary explicitly accepted or closed;
- [ ] DNS and exact certificates verified;
- [ ] final public build-time variables set and web rebuilt;
- [ ] production borrower keys load as the non-root API user;
- [ ] `BORROWER_REAL_DATA_ENABLED=false` confirmed;
- [ ] Nginx site collision reviewed;
- [ ] `nginx -t` passed before reload;
- [ ] apex, `www`, `apply`, and API external probes passed;
- [ ] external internal-port probes failed as required;
- [ ] logs passed PII/secret review;
- [ ] WordPress rollback was proven and remains immediately available;
- [ ] PostgreSQL, MinIO, hosted-Auth, and key backup/restore ownership recorded.

Any unchecked item is a documented gap, not an implied pass.
