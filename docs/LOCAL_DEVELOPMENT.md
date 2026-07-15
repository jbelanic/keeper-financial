# Local Development

## Services

The application PostgreSQL database listens on `5432`. Supabase CLI runs local identity services separately (`54321`) and its own internal database (`54322`). This keeps Supabase identity distinct from the application’s authorization data.

1. Copy `.env.example` to `.env`; use only local, non-sensitive values.
2. Run `make bootstrap`.
3. Run `supabase start` and replace the placeholder local anon key in `.env` with the CLI output.
4. Run `docker compose up -d db`.
5. Run `make migrate && make seed`.
6. Run `make api-dev` and `make web-dev` in separate terminals.

For Linux containers, Compose maps `host.docker.internal` to the host so the API can fetch the local Supabase JWKS. The expected JWT issuer remains the issuer embedded by local Supabase.

## Synthetic data

`make seed` exits unless `APP_ENV=local`. Seed email addresses use `example.test`, postings remain `draft`, licence text explicitly says it is synthetic, and no borrower or real candidate data is created.

The Phase 0 seed does not create Supabase Auth users. To exercise the web sign-in end to end, create a local Supabase user, then deliberately link its subject to a local `UserIdentity` and assign the appropriate local role. This manual relationship step is intentional: identity alone must fail authorization.

For API-only local checks, `X-Dev-Auth-Sub` may identify a seeded subject while local development authentication is enabled. Never enable this mechanism outside local.

The `/admin/leads` page remains behind the admin layout and obtains its bearer token on the server. For API-only testing, an active verified local user with `brokerage_admin` may call `GET /api/v1/leads` or the lead-specific marketing-withdrawal route using the local development subject header. Set `X-Dev-Auth-AAL: aal2` when exercising the nonlocal-equivalent MFA policy. Do not place contact data in queue query strings; supported web filters are only `page` and `status`.

## Database changes

Change SQLAlchemy models and create an Alembic revision. Apply with `make migrate`; confirm model/revision alignment with `make migrate-check`. Never edit an issued production migration to reshape an already-deployed database.

Phase 1B adds revision `20260714_0002` for deterministic lead queue ordering/filter indexes; the issued `20260714_0001` foundation remains unchanged.

After changing FastAPI routes or schemas, run `make openapi`. It exports OpenAPI, regenerates TypeScript declarations, and formats the contract package so a second run should produce no drift.

## Private documents

Local objects live only under `storage/dev_uploads`, which is ignored except for `.gitkeep`. Random keys—not filenames—address objects. Retrieval always goes through the authenticated API and quarantined files are denied. Local storage is rejected by nonlocal configuration validation.

## Troubleshooting

- `supabase: command not found`: install the official Supabase CLI before identity testing.
- API database health is `503`: start PostgreSQL and apply migrations.
- Portal redirects to sign-in after successful identity login: confirm a verified local `UserIdentity`, role, active user, and permitted candidate state exist.
- Mortgage application endpoint is `503`: expected until an approved HTTPS provider and allow-listed host are configured.
- Agent-attributed apply/redirect returns validation or unavailable behavior: confirm the slug grammar, a published `AgentProfile` for lead attribution, and a separately approved `MORTGAGE_APPLICATION_AGENT_LINKS` entry for redirect attribution.
