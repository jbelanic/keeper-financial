# Environment Variable Reference

`.env.example` is the executable reference. `.env` files are ignored. Values prefixed `NEXT_PUBLIC_` are browser-visible and must never contain secrets.

| Group | Variables | Rule |
|---|---|---|
| Tier | `APP_ENV`, `DEBUG`, `DEV_AUTH_ENABLED`, `REQUIRE_ADMIN_MFA` | Nonlocal rejects debug/dev auth and requires admin MFA. |
| Origins | `WEB_ORIGIN`, `CORS_ORIGINS` | Nonlocal requires HTTPS, no loopback, and no wildcard. |
| Database | `DATABASE_URL` | Application PostgreSQL connection; secret outside local. |
| Supabase | `SUPABASE_ISSUER`, `SUPABASE_AUDIENCE`, `SUPABASE_JWKS_URL`, `SUPABASE_JWT_ALGORITHMS` | API accepts only configured asymmetric algorithms, issuer, and audience. |
| Lead abuse guard | `LEAD_RATE_LIMIT_REQUESTS`, `LEAD_RATE_LIMIT_WINDOW_SECONDS`, `LEAD_RATE_LIMIT_TRACKED_CLIENTS` | Always-on, bounded process-local limiter. The API keys only on the direct peer and never trusts forwarding headers. |
| Web identity | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` | The anon key is intended for a browser; it is not authorization. |
| Storage | `STORAGE_BACKEND`, `LOCAL_STORAGE_PATH`, `PUBLIC_OBJECT_URLS_ENABLED`, `MAX_DOCUMENT_BYTES`, `ALLOWED_DOCUMENT_MIME_TYPES` | Local backend only in local. Public object URLs always fail validation. Phase 1C permits only the exact PDF, DOC, and DOCX MIME allow-list and caps files at 10 MiB. |
| Local Compose storage owner | `LOCAL_UID`, `LOCAL_GID` | Local Docker Compose only. Defaults to `1000:1000`; set to the host `id -u`/`id -g` so the non-root API can write the bind-mounted ignored storage directory without world-writable permissions. |
| Malware scan | `MALWARE_SCANNER_BACKEND` | `local_test` is deterministic local/test plumbing and is prohibited nonlocally. `disabled` is the only honest nonlocal value until an approved production adapter exists; upload then fails closed before storage/metadata success. |
| R2 | `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_REGION`, `SIGNED_URL_TTL_SECONDS` | All required for R2. Bucket must be private; TTL is 30–300 seconds. |
| Mortgage provider | `MORTGAGE_APPLICATION_PROVIDER`, `MORTGAGE_APPLICATION_URL`, `MORTGAGE_APPLICATION_ALLOWED_HOSTS`, `MORTGAGE_APPLICATION_AGENT_LINKS` | The owner-approved brokerage-wide destination is `https://apply.keeperfinancial.ca/`. Destinations require HTTPS, exact allow-list match, and no query/fragment/credentials. Agent links remain empty unless separately approved and are never request-provided destinations. |
| Deferred providers | `ESIGN_PROVIDER`, `CRM_PROVIDER` | Adapter labels only; `disabled` is the honest default. |
| Web/API | `API_INTERNAL_URL`, `NEXT_PUBLIC_API_BASE_URL` | Server and browser API locations. |
| Public site | `NEXT_PUBLIC_SITE_URL`, `NEXT_PUBLIC_BROKERAGE_DISPLAY_NAME`, `NEXT_PUBLIC_BROKERAGE_LEGAL_NAME`, `NEXT_PUBLIC_BROKERAGE_REGULATORY_TEXT`, `NEXT_PUBLIC_PUBLIC_ADDRESS`, `NEXT_PUBLIC_PUBLIC_EMAIL`, `NEXT_PUBLIC_PUBLIC_PHONE`, `NEXT_PUBLIC_PUBLIC_PHONE_E164`, `NEXT_PUBLIC_MORTGAGE_APPLICATION_URL` | Browser-visible owner-supplied public facts. Source defaults match the supplied approved values; invalid URL overrides fail back to approved configuration. |
| Optional public values | `NEXT_PUBLIC_BOOKING_URL`, `NEXT_PUBLIC_PRINCIPAL_BROKER` | Empty by default. Invalid/missing booking URLs and blank principal-broker values are not rendered. No booking vendor or principal broker is inferred. |

For `staging_non_sensitive` and `production`, startup fails unless R2 credentials/endpoints, hosted Supabase endpoints, HTTPS origins, disabled development authentication, disabled debug, and mandatory admin MFA are configured safely. Candidate upload additionally requires a future approved nonlocal malware-scanner adapter; the current `disabled` value makes upload unavailable rather than implying scanning. Mortgage, CRM, and e-signature providers may remain disabled; their features then fail explicitly and safely.
