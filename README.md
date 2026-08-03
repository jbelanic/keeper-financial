# Keeper Financial

Keeper Financial is a Next.js/FastAPI modular monolith. The owner-approved live/production environment is Docker on the local Linux host: Compose PostgreSQL for application data, Compose MinIO for private objects, Compose ClamAV for pre-persistence document scanning, and the repository-tracked local Supabase CLI stack for Auth. Hosted Supabase, Cloudflare R2, and remote cloud infrastructure are not supported.

`docs/00_PROJECT_SOURCE_OF_TRUTH.md` is authoritative. On 2026-07-24 the owner approved Keeper becoming the MVP system of record for borrower application intake and supporting documents under `docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md`. That workflow is not implemented at the Phase A documentation checkpoint. Credit-bureau connectivity, automated underwriting/approval, lender submission, deal compliance, custom e-signature, commissions, payroll, and a full client CRM remain excluded.

## Repository

```text
apps/web             Next.js React/TypeScript application
apps/api             FastAPI, SQLAlchemy, and Alembic
packages/ui          Accessible components and design tokens
packages/contracts   Generated OpenAPI/TypeScript contract boundary
infrastructure       Application Dockerfiles
supabase              Local Supabase CLI/Auth configuration
docs                  Governing architecture and operations documentation
```

## Linux prerequisites

- Docker Engine with Compose
- Node-invoked Supabase CLI (`npx supabase`; verified with 2.109.1)
- Node.js 22+ and npm 10+ plus Python 3.12–3.14 only for host-side development/tests

If Docker reports socket permission denied, the requested one-line immediate activation is:

```bash
sudo usermod -aG docker "$USER" && newgrp docker
```

This repository never runs that command. Logging out and back in after `usermod` is the cleaner persistent group-session activation. Do not put real credentials in the repository. `.env` and `supabase/signing_keys.json` are ignored.

## Live local bootstrap

```bash
cp .env.example .env
${EDITOR:-vi} .env
(umask 077 && test -e supabase/signing_keys.json || printf '[]\n' > supabase/signing_keys.json)
npx supabase gen signing-key --algorithm ES256
npx supabase start
npx supabase status
docker compose config --quiet
make infra
make migrate
docker compose run --rm api alembic current --check-heads
make up
docker compose ps --all
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/health/db
curl --fail http://localhost:9000/minio/health/live
.venv/bin/python apps/api/scripts/verify_clamav.py --host 127.0.0.1 --port 3310
```

Supabase CLI 2.109.1 reads a configured signing-key file before first generation, so the preceding guarded command creates a private-permission, non-secret empty JSON key array only when the ignored file is absent. The exact generation command then replaces it with ES256 key material; never print, inspect, copy, stage, or commit that file. Replace all `.env` `change-me` values, then manually copy only the browser-safe local anon key reported by `npx supabase status` into `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Never put the service-role key, secret key, JWT secret, or signing key in a `NEXT_PUBLIC_*` variable. Rebuild `web` whenever a public value changes because Next.js embeds it during the image build.

`make infra` starts healthchecked PostgreSQL, MinIO, and ClamAV plus the idempotent private-bucket initializer. The first ClamAV start with an empty named signature volume may take several minutes. `make migrate` explicitly rebuilds the current API image before running the non-destructive-by-default Alembic upgrade, preventing an older local image from reporting or applying a stale migration head. Migrations never run automatically on service startup. The web container uses internal API and Supabase routes for server rendering while retaining loopback-only browser URLs. Open `http://localhost:3000`; the tracked Compose configuration binds application, database, object, and clamd ports to loopback. Recreate older containers before assuming their live bindings match the current file.

The default Compose stack is safe for side-by-side validation beside an existing public web server: it does not bind loopback `443` and does not require the Documenso TLS bridge while `ESIGN_PROVIDER=disabled`. If an approved Documenso ceremony is required, include the opt-in overlay explicitly with `docker compose -f compose.yaml -f compose.documenso.yaml ...`. See `docs/DEPLOYMENT_SIDE_BY_SIDE.md` for pre-cutover `.env` values, SSH-tunnel validation, and the separate host-managed Nginx cutover step.

The source baseline for the borrower Phase A decision is `main` at `5f8a41f34bb3586c59d613848fafc9435a86b50d`, merged through PR #9. It includes candidate authentication and posting-bound provisioning, candidate/administrator MFA, exact-application review/onboarding completion, agent eligibility/profile workflows, strict ClamAV/MinIO candidate-document handling, migrations through `20260722_0010`, and approved public-content updates.

The current baseline has one Alembic head at `20260722_0010`; historical migration and contract evidence for earlier checkpoints remains preserved in the dated reports. Neither source acceptance nor Git publication authorizes deployment, shared-database migration, production/pilot operation, real-person activation, credential/external-service changes, or legal/privacy/regulatory/claims/accessibility approval. Current limitations are tracked in `docs/15_KNOWN_LIMITATIONS.md`.

The approved next borrower gate is Phase B secure foundation. The repository is not approved to receive real borrower data: exact consent wording, implementation, host hardening, key custody, authentication/email configuration, backup/restore/purge, monitoring, incident response, retention/legal-hold operations, accessibility and legal/privacy/regulatory review, browser evidence, and owner go/no-go approval remain outstanding. Supabase CLI ports still require host-firewall protection, the upstream CLI stack is not production-hardened, and local SMTP is capture rather than real delivery.

The API container database URL has this shape:

```text
postgresql+psycopg://keeper:<redacted>@db:5432/keeper
```

## Validation

The tracked example can be rendered without reading `.env` or printing its values:

```bash
KEEPER_ENV_FILE=.env.example docker compose --env-file .env.example config --quiet
```

Host-side application checks remain available:

```bash
make bootstrap
make lint
make typecheck
make test
make build
git diff --check
```

## Shutdown

```bash
docker compose down
npx supabase stop
```

These commands preserve named data volumes. Do not add `--volumes` unless permanent local PostgreSQL/MinIO deletion is intentional.

See [side-by-side deployment](docs/DEPLOYMENT_SIDE_BY_SIDE.md), [local operations](docs/LOCAL_DEVELOPMENT.md), [environment variables](docs/11_ENVIRONMENT_VARIABLES.md), and [known limitations](docs/15_KNOWN_LIMITATIONS.md).
