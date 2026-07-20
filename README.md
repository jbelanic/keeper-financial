# Keeper Financial

Keeper Financial is a Next.js/FastAPI modular monolith. The owner-approved live/production environment is Docker on the local Linux host: Compose PostgreSQL for application data, Compose MinIO for private objects, Compose ClamAV for pre-persistence document scanning, and the repository-tracked local Supabase CLI stack for Auth. Hosted Supabase, Cloudflare R2, and remote cloud infrastructure are not supported.

`docs/00_PROJECT_SOURCE_OF_TRUTH.md` is authoritative. Product boundaries remain unchanged: this repository does not implement mortgage origination, borrower financial-data/document collection, lender submission, custom e-signature, commissions, or a client CRM.

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

`make infra` starts healthchecked PostgreSQL, MinIO, and ClamAV plus the idempotent private-bucket initializer. The first ClamAV start with an empty named signature volume may take several minutes. `make migrate` is the explicit, non-destructive-by-default Alembic upgrade command inside the API image. Migrations never run automatically on service startup. Open `http://localhost:3000`; the tracked Compose configuration binds application, database, object, and clamd ports to loopback. Recreate older containers before assuming their live bindings match the current file.

The current merged baseline is `main` at `3331519de482c2bd062b7b7e10e067f06c42f9a3`; it includes the implementation merge at `b906027`, candidate authentication and posting-bound provisioning, candidate and administrator MFA, application-specific review/onboarding workflows, strict ClamAV/MinIO document handling, and forward schema reconciliation through migration `20260718_0007`.

The owner has explicitly accepted the Phase 1 source implementation, including the administrator/operator workflow refinement on `feat/admin-workflow-operator-ux`. At the verified acceptance-reconciliation state, the refinement remains uncommitted and unmerged and advances the candidate migration head to `20260719_0008`; the recorded evidence reports one Alembic head and deterministic migration/contract verification. Source acceptance does not authorize commit, push, pull request, merge, history rewriting, deployment, shared-database migration, production/pilot operation, final activation or lifecycle/role transition, credential/external-service changes, or legal/privacy/regulatory/claims/accessibility approval. Earlier dated evidence remains historical; current limitations are tracked in `docs/15_KNOWN_LIMITATIONS.md`.

Phase 1F production and controlled-pilot readiness planning is the next gate. Its draft evidence and decision plan is recorded in `docs/26_PHASE_1F_PRODUCTION_AND_CONTROLLED_PILOT_READINESS_PLAN.md`; Phase 1F implementation remains prohibited until the plan, evidence requirements, owner decisions, scope, and acceptance criteria are approved. The repository is not production-approved or deployed: host hardening, production authentication/email configuration, backup/restore, monitoring, incident response, retention operations, accessibility and legal/privacy/regulatory review, pilot evidence, and owner go/no-go approval remain outstanding. Final activation, candidate-to-agent transition, and agent-role grant remain separately deferred outside Phase 1F rather than readiness work. Supabase CLI ports still require host-firewall protection, the upstream CLI stack is not production-hardened, and local SMTP is capture rather than real delivery.

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

See [local operations](docs/LOCAL_DEVELOPMENT.md), [environment variables](docs/11_ENVIRONMENT_VARIABLES.md), and [known limitations](docs/15_KNOWN_LIMITATIONS.md).
