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
- Borrower application metadata, encrypted draft payloads, capabilities, attribution, assignment, lifecycle, document metadata, retention, and legal holds.

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

Supabase Studio is optional local-operator tooling only and must not be exposed as a public, shared, or application-facing service. Supabase Storage and its S3 protocol remain disabled; they are not application storage and must not replace MinIO.

## Object storage

The live object store is the `minio` service in `compose.yaml`. PostgreSQL stores metadata; MinIO stores bytes. Borrower documents use a dedicated private bucket or least-privilege namespace, and immutable submitted application snapshots are encrypted before MinIO persistence. The API uses the S3-compatible interface with path-style addressing, the `minio` service name for container traffic, and a loopback host endpoint only when producing short-lived browser download URLs. Local filesystem storage remains a test/development fallback only.

The live malware-scanning boundary is the `clamav` Compose service. The API sends bounded in-memory bytes to `clamd` over the internal `clamav:3310` TCP endpoint using framed `INSTREAM`; port 3310 is published on loopback only for operator verification. Candidate bytes are not written to MinIO until type/structure validation and a clean scan both succeed.

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

## Keeper-native borrower application

The same repository and release process will serve `https://apply.keeperfinancial.ca`. After implementation and acceptance, the public `/apply` page must enter that exact Keeper-owned origin; no external-provider redirect, Filogix handoff, export, or API integration is required in the MVP. At Phase A this is target architecture only, and current code still contains the legacy external redirect.

Borrowers use a high-entropy capability stored only in a secure host-only cookie, while PostgreSQL stores a keyed digest bound to one draft. The capability is not identity verification and grants no internal access. Exact host/origin, CSRF, rate-limit, expiry, revision, and lifecycle checks remain mandatory.

PostgreSQL holds encrypted mutable drafts and authoritative metadata. Private MinIO holds encrypted documents and immutable encrypted submission snapshots. Because borrower objects contain application-layer ciphertext, authorized downloads are API-proxied decryptions rather than direct presigned MinIO URLs. Agent attribution is resolved from an eligible public slug on the server; internal reads require exact assignment or administrator authority and AAL2.

## E-signature

Use the server-side adapter boundary. The selected provider is self-hosted
Documenso or `disabled`. The adapter accepts one configured API base URL and
token, constructs only the exact allow-listed envelope-status URL, rejects
redirects, bounds response size and timeout, verifies the returned envelope ID,
and accepts only deployed-version-confirmed statuses. Provider or network
ambiguity fails closed and never marks an agreement complete.

Envelope records belong to one exact onboarding assignment. Replacement creates
a new current envelope and retains the rejected predecessor as non-satisfying
history. Webhooks are not implemented until the deployed Documenso version's
exact event names and signature scheme are separately confirmed.

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

This is the approved deployment target and an implemented local topology, not evidence of production deployment or release approval. Phase 1F must define and approve the production and controlled-pilot operating plan, evidence, owners, and go/no-go criteria before release.

There are two application modes: `local` for isolated development/tests and `production` for the live local Docker deployment. There is no remote staging or hosted production tier.

The approved target topology is one Docker Compose project on the self-hosted Linux host, fronted by an exact-host TLS ingress for `keeperfinancial.ca` and `apply.keeperfinancial.ca`:

- `web` calls `api` at `http://api:8000` for server-side traffic; browsers use `http://localhost:8000`.
- `api` connects to PostgreSQL at the `db` service using `postgresql+psycopg` and to MinIO at `http://minio:9000`.
- `db` and `minio` use durable named volumes and healthchecks.
- `minio-init` idempotently creates the configured private bucket and disables anonymous access before API startup; MinIO API CORS uses the server's `MINIO_API_CORS_ALLOW_ORIGIN` environment variable with the exact loopback web origin.
- browsers access the existing local Supabase CLI Auth endpoint through loopback; the API fetches JWKS through `host.docker.internal`. The CLI owns its separate port bindings, which require host-firewall protection.
- only ingress ports 80/443 are public; API, database, MinIO, MinIO Console, clamd, Studio, and other operator surfaces remain private or loopback-only.

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
- `borrower_applications`

## Future CRM boundary

Do not create a full CRM in Phase 1.

Expose a future event/adapter boundary for:

- Lead created.
- Lead assigned.
- Candidate activated as agent.
- Agent profile published.
- Keeper borrower application submitted and assigned.

No Filogix or credit-bureau implementation is required in the borrower MVP.
