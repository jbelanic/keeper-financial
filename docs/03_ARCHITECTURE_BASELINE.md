# Architecture Baseline

## Architectural style

Use a modular monolith for Phase 1.

Do not introduce microservices. Keep bounded modules inside one FastAPI service and one web application unless a proven constraint requires separation.

## Recommended repository

```text
apps/web
apps/api
packages/ui
packages/contracts
infrastructure
docs
```

## Web application

Preferred baseline:

- React.
- TypeScript.
- SEO-capable server rendering or static generation.
- Public and authenticated route groups.
- Shared design tokens and components.
- Typed API client.
- Accessible forms and validation.
- No sensitive application state in browser persistence unless justified.

## API

- FastAPI.
- Versioned `/api` routes.
- SQLAlchemy 2.x style.
- Alembic migrations.
- Pydantic schemas.
- Service-layer lifecycle enforcement.
- Repository/data-access boundaries only where they reduce complexity.
- OpenAPI enabled in local and controlled non-production environments.
- Request IDs and structured logs.

## Database

PostgreSQL is authoritative for:

- Application users.
- Roles.
- Candidate state.
- Recruitment postings.
- Onboarding.
- Controlled document metadata.
- Agent profile approval.
- Lead inquiries.
- Consent evidence.
- Audit events.

Do not store raw object files in PostgreSQL.

## Identity and authorization

### Identity

The repository-tracked local Supabase CLI stack supplies:

- Sign-up/sign-in.
- Email verification.
- Password reset.
- Token issuance.

### Authorization

The API verifies the Supabase JWT and maps the subject to:

- Local user.
- Active state.
- Role assignment.
- Candidate or brokerage relationship.
- Resource-level access.

No active application relationship means no portal entry.

The current web and API code genuinely depends on Supabase Auth token/session semantics. The supported live approach is therefore the checked-in `supabase/config.toml` started locally on the same Linux host. Hosted Supabase is prohibited. The API reaches its JWKS endpoint through the Docker host gateway while validating the issuer embedded by the local Auth service.

## Object storage

The live object store is the `minio` service in `compose.yaml`. PostgreSQL stores metadata; MinIO stores bytes. The API uses the S3-compatible interface with path-style addressing, the `minio` service name for container traffic, and a loopback host endpoint only when producing short-lived browser download URLs. Local filesystem storage remains a test/development fallback only.

Required:

- Private bucket.
- Random object keys.
- Metadata in PostgreSQL.
- Authorization before upload/download.
- Short-lived signed URLs or API proxy.
- Content-type and size validation.
- Malware-scanning integration point.
- No original filename as the object key.
- No public URL.

## External mortgage application

Configuration controls:

- Provider name.
- Brokerage-wide application URL.
- Allowed hostnames.
- Optional agent-specific URL mapping.
- Availability state.

The API or server-rendered route validates redirects. Never allow arbitrary query-provided destinations.

## E-signature

Use an adapter boundary. Initial supported modes may be:

- `external_manual`
- `docusign`
- `adobe_sign`
- `disabled`

Do not represent a typed name or checkbox as a legal electronic signature unless approved requirements and legal review support that use.

## Email

Use a transactional email abstraction.

Email must not include:

- Sensitive candidate documents.
- Raw private object URLs.
- Mortgage financial information.
- Authentication tokens in logs.

## Observability

- `/health`.
- `/health/db`.
- Structured application logs.
- Error monitoring selected later.
- Audit events are not a substitute for logs.
- Logs are not a substitute for audit events.

## Deployment topology

There are two application modes: `local` for isolated development/tests and `production` for the live local Docker deployment. There is no remote staging or hosted production tier.

The production topology is one Docker Compose project on the local Linux host:

- `web` calls `api` at `http://api:8000` for server-side traffic; browsers use `http://localhost:8000`.
- `api` connects to PostgreSQL at the `db` service using `postgresql+psycopg` and to MinIO at `http://minio:9000`.
- `db` and `minio` use durable named volumes and healthchecks.
- `minio-init` idempotently creates the configured private bucket and disables anonymous access before API startup; MinIO API CORS uses the server's `MINIO_API_CORS_ALLOW_ORIGIN` environment variable with the exact loopback web origin.
- browsers access the existing local Supabase CLI Auth endpoint through loopback; the API fetches JWKS through `host.docker.internal`. The CLI owns its separate port bindings, which require host-firewall protection.

Production validation fails closed when debug/development auth is enabled, admin MFA is not required, local file storage is selected, public object URLs are enabled, required local-service settings are missing, or database/Auth/storage URLs do not match this topology. Alembic migrations are an explicit operator action and never run automatically during service startup.

## API modules

Suggested initial modules:

- `auth`
- `users`
- `recruitment`
- `candidates`
- `onboarding`
- `documents`
- `agents`
- `leads`
- `consents`
- `audit`
- `health`
- `integrations`

## Future CRM boundary

Do not create a full CRM in Phase 1.

Expose a future event/adapter boundary for:

- Lead created.
- Lead assigned.
- Candidate activated as agent.
- Agent profile published.
- External mortgage application started where supported.

No vendor-specific implementation is required in Phase 1.
