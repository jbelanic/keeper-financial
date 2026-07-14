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

Supabase Auth supplies:

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

## Object storage

### Local

Local development may store files under a configured local-only directory.

### Nonlocal

Use a private Cloudflare R2-compatible bucket.

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

## Deployment tiers

Minimum:

- `local`
- `staging_non_sensitive`
- `production`

Nonlocal tiers must fail startup when:

- Development-header authentication is enabled.
- Local file storage is selected.
- public object URLs are enabled;
- loopback origins are configured;
- required secrets are missing;
- CORS is overly broad;
- unsafe debug mode is enabled.

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
