# Keeper Financial

Keeper Financial is a Next.js/FastAPI modular monolith. The owner-approved live/production environment is Docker on the local Linux host: Compose PostgreSQL for application data, Compose MinIO for private objects, and the repository-tracked local Supabase CLI stack for Auth. Hosted Supabase, Cloudflare R2, and remote cloud infrastructure are not supported.

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
```

Supabase CLI 2.109.1 reads a configured signing-key file before first generation, so the preceding guarded command creates a private-permission, non-secret empty JSON key array only when the ignored file is absent. The exact generation command then replaces it with ES256 key material; never print, inspect, copy, stage, or commit that file. Replace all `.env` `change-me` values, then manually copy only the browser-safe local anon key reported by `npx supabase status` into `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Never put the service-role key, secret key, JWT secret, or signing key in a `NEXT_PUBLIC_*` variable. Rebuild `web` whenever a public value changes because Next.js embeds it during the image build.

`make infra` starts healthchecked PostgreSQL and MinIO plus the idempotent private-bucket initializer. `make migrate` is the explicit, non-destructive-by-default Alembic upgrade command inside the API image. Migrations never run automatically on service startup. Open `http://localhost:3000`; the tracked Compose configuration binds application, database, and object ports to loopback. Recreate older containers before assuming their live bindings match the current file.

Live evidence on 2026-07-16 confirmed that the tracked Supabase project starts with CLI 2.109.1, Auth health succeeds, and JWKS returns HTTP `200` with exactly one ES256 key. Rebuilt/recreated web and API, PostgreSQL, and MinIO are healthy and loopback-bound; `minio-init` exited `0`; web `/` and `/agents` return success; and API `/health/db` reports reachable. `alembic upgrade head` and `alembic current --check-heads` reached `20260717_0005`; clean-environment API pytest and all 77 Vitest tests passed. `alembic check` is not green: it reports pre-existing Phase 1D model/schema drift involving indexes and foreign-key `ondelete`. Keep it as a diagnostic; it is not a fresh-bootstrap blocker and this deployment update does not rewrite historical schema behavior. Supabase CLI ports still bind broadly and require host-firewall protection; the upstream CLI stack is not production-hardened, local SMTP is capture rather than real delivery, and candidate uploads fail closed until an approved scanner exists.

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
