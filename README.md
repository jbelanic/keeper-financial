# Keeper Financial

Phase 1C engineering implementation for Keeper Financial recruitment postings, verified candidate provisioning, posting-specific applications, private candidate documents, status, and withdrawal. The Phase 1B lead flow, Phase 1A public website, and Phase 0 security foundation remain preserved. This repository intentionally does **not** implement candidate review/onboarding decisions, mortgage origination, borrower financial-data collection, lender submission, custom e-signature, commission calculation, or a client CRM.

`docs/00_PROJECT_SOURCE_OF_TRUTH.md` remains authoritative. Start with [the Phase 1C report](docs/20_PHASE_1C_IMPLEMENTATION_REPORT.md) and the immutable [candidate application policy](docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md). Historical evidence remains in the [Phase 1B](docs/18_PHASE_1B_IMPLEMENTATION_REPORT.md), [Phase 1A](docs/17_PHASE_1A_IMPLEMENTATION_REPORT.md), and [Phase 0](docs/16_PHASE_0_IMPLEMENTATION_REPORT.md) reports.

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

The local public site uses the owner-supplied Keeper Financial identity, contact details, and allow-listed secure application destination from `.env.example`. Public content is typed and repository-controlled in `apps/web/lib/public-content.ts`; public facts are validated in `apps/web/lib/site-config.ts`. A booking action remains absent unless an owner-supplied HTTPS URL passes the existing fail-closed validation. `/apply?agent=<safe-slug>` may carry only a grammar-checked attribution slug; the API still requires a published profile for lead attribution and a separately configured mapping for redirects.

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

The exact Phase 1C validation evidence is documented in `docs/20_PHASE_1C_IMPLEMENTATION_REPORT.md`.

The API OpenAPI document is exported into `packages/contracts/openapi.json`; `openapi-typescript` then creates and formats `packages/contracts/src/generated.ts`. Regenerate contracts with `make openapi` whenever a route or schema changes.

## Local authorization boundary

Supabase proves identity; it never grants portal access by itself. The API also requires an active, verified local `UserIdentity`, the appropriate `Role`/`UserRole`, the required `Candidate` relationship, and an allowed lifecycle state. Development identity headers work only when both `APP_ENV=local` and `DEV_AUTH_ENABLED=true`.

The protected admin and candidate pages obtain the Supabase access token through the supported SDK and call FastAPI with no-store behavior. Candidate registration proves provider identity only; the published-posting start boundary atomically creates the narrow local candidate relationship. Application/document ownership, lifecycle, server-owned privacy evidence, candidate document AAL2, and admin role/AAL2 rules remain API-authoritative.

See [local development](docs/LOCAL_DEVELOPMENT.md), [environment variables](docs/11_ENVIRONMENT_VARIABLES.md), and [known limitations](docs/15_KNOWN_LIMITATIONS.md).
