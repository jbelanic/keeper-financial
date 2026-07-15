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

`make seed` exits unless `APP_ENV=local`. Seed email addresses use `example.test`; recruitment fixtures are conspicuously titled `SYNTHETIC` and cover published, draft, closed, and archived visibility plus one synthetic candidate draft. They are not real job postings or candidates. No borrower data is created. The seed is idempotent.

The Phase 0 seed does not create Supabase Auth users. To exercise the web sign-in end to end, create a local Supabase user, then deliberately link its subject to a local `UserIdentity` and assign the appropriate local role. This manual relationship step is intentional: identity alone must fail authorization.

For API-only local checks, `X-Dev-Auth-Sub` may identify a seeded subject while local development authentication is enabled. Never enable this mechanism outside local.

Candidate application start additionally uses `X-Dev-Auth-Email` and `X-Dev-Auth-Verified: true` to emulate a verified provider identity. Candidate document upload/list/download requires `X-Dev-Auth-AAL: aal2`. These headers are accepted only when both `APP_ENV=local` and `DEV_AUTH_ENABLED=true`; production trusts only verified signed claims.

The `/admin/leads` page remains behind the admin layout and obtains its bearer token on the server. For API-only testing, an active verified local user with `brokerage_admin` may call `GET /api/v1/leads` or the lead-specific marketing-withdrawal route using the local development subject header. Set `X-Dev-Auth-AAL: aal2` when exercising the nonlocal-equivalent MFA policy. Do not place contact data in queue query strings; supported web filters are only `page` and `status`.

## Database changes

Change SQLAlchemy models and create an Alembic revision. Apply with `make migrate`; confirm model/revision alignment with `make migrate-check`. Never edit an issued production migration to reshape an already-deployed database.

Phase 1B adds issued revision `20260714_0002` for lead queue indexes. Phase 1C adds `20260715_0003` for posting evidence/indexes, mandatory application provenance and attempts, typed questionnaire entries, application-specific history, and candidate document linkage/category/scan metadata. Issued `20260714_0001` and `20260714_0002` remain unchanged.

After changing FastAPI routes or schemas, run `make openapi`. It exports OpenAPI, regenerates TypeScript declarations, and formats the contract package so a second run should produce no drift.

## Private documents

Local objects live only under `storage/dev_uploads`, which is ignored except for `.gitkeep`. Random keys—not filenames—address objects. Candidate uploads permit only optional résumé/cover-letter PDF/DOC/DOCX files up to 10 MiB after extension, declared MIME, and signature agreement. Retrieval always goes through the authenticated AAL2 API; quarantined/non-clean files are denied.

`MALWARE_SCANNER_BACKEND=local_test` is explicitly a deterministic local/test decision adapter, not production malware scanning. Nonlocal environments must not use it. Until an approved nonlocal adapter exists, configure `disabled`; candidate uploads then fail closed before object/metadata success.

## Troubleshooting

- `supabase: command not found`: install the official Supabase CLI before identity testing.
- API database health is `503`: start PostgreSQL and apply migrations.
- Portal redirects to sign-in after successful identity login: confirm a verified local `UserIdentity`, role, active user, and permitted candidate state exist.
- Mortgage application endpoint is `503`: expected until an approved HTTPS provider and allow-listed host are configured.
- Agent-attributed apply/redirect returns validation or unavailable behavior: confirm the slug grammar, a published `AgentProfile` for lead attribution, and a separately approved `MORTGAGE_APPLICATION_AGENT_LINKS` entry for redirect attribution.
