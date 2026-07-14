# Keeper Financial

Phase 0 foundation for Keeper Financial’s public website, candidate portal, and brokerage administration portal. This repository intentionally does **not** implement mortgage origination, borrower financial-data collection, lender submission, custom e-signature, commission calculation, or a client CRM.

`docs/00_PROJECT_SOURCE_OF_TRUTH.md` remains authoritative. Start with [the Phase 0 report](docs/16_PHASE_0_IMPLEMENTATION_REPORT.md) for the implemented boundary.

## Repository

```text
apps/web             Next.js React/TypeScript application
apps/api             FastAPI modular monolith, SQLAlchemy, Alembic
packages/ui          Accessible components and design tokens
packages/contracts   OpenAPI-to-TypeScript generation boundary
infrastructure       Container definitions
supabase              Local Supabase CLI configuration
storage/dev_uploads  Git-ignored local-only private object storage
docs                  Governing baseline and Phase 0 operating documentation
```

## Prerequisites

- Node.js 22 LTS or newer supported release below 25
- npm 10+
- Python 3.12–3.14
- Docker with Compose
- Supabase CLI for local identity

No production credentials belong in this repository.

## First local run

```bash
cp .env.example .env
make bootstrap
supabase start
docker compose up -d db
make migrate
make seed
make api-dev
```

In another terminal:

```bash
make web-dev
```

Open `http://localhost:3000`; API documentation is local-only at `http://localhost:8000/docs`. The synthetic seed subjects support direct local API authorization-header testing. They are not real Supabase accounts.

To run all containerized application services after creating `.env` and starting local Supabase:

```bash
docker compose up --build
```

## Validation

```bash
make format
make lint
make typecheck
make test
make migrate-check
make build
make openapi
```

The API OpenAPI document is exported into `packages/contracts/openapi.json`; `openapi-typescript` then creates `packages/contracts/src/generated.ts`. Regenerate contracts whenever a route or schema changes.

## Local authorization boundary

Supabase proves identity; it never grants portal access by itself. The API also requires an active, verified local `UserIdentity`, the appropriate `Role`/`UserRole`, the required `Candidate` relationship, and an allowed lifecycle state. Development identity headers work only when both `APP_ENV=local` and `DEV_AUTH_ENABLED=true`.

See [local development](docs/LOCAL_DEVELOPMENT.md), [environment variables](docs/11_ENVIRONMENT_VARIABLES.md), and [known limitations](docs/15_KNOWN_LIMITATIONS.md).
