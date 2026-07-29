# Local Docker Operations

The local Linux Docker deployment is the live/production target. PostgreSQL (`db`) is the application database, MinIO (`minio`) is the private object store, ClamAV (`clamav`) scans documents before persistence, and the checked-in Supabase CLI configuration supplies Auth because the current browser session and API JWT code requires Supabase semantics. The Supabase stack's internal database remains separate from the application database.

Compose publishes PostgreSQL, MinIO, clamd, API, and web ports on loopback only. Clamd TCP has no authentication or encryption, so port 3310 must remain loopback-only. The Supabase CLI manages its own port bindings; protect them with the Linux host firewall and do not expose any stack service to an untrusted network. [Upstream Supabase documentation](https://supabase.com/docs/guides/local-development/cli-workflows) describes its CLI stack as development-only rather than production-hardened; this is an explicit limitation of the owner-selected local-only model, not an implied security certification. [ClamAV's Docker documentation](https://docs.clamav.net/manual/Installing/Docker.html) documents the official image, `/var/lib/clamav` signature database, TCP 3310, and daemon health behavior.

## Linux Mint continuation and portability

The current checkpoint has been reconstructed and operated successfully on Linux Mint. Use Docker Engine with the Compose plugin, not assumptions tied to Docker Desktop. Run from the repository checkout on the Linux filesystem, confirm the current user can access the Docker socket, and retain the `host.docker.internal:host-gateway` mapping used by the API to reach local Supabase JWKS.

Linux Mint portability requirements:

- loopback ports `3000`, `5432`, `8000`, `9000`, `9001`, and `3310` must be available for the Compose stack;
- the configured local Supabase ports, including Auth/API `54321`, Studio `54323` when enabled, and Mailpit `54324`, must remain host-local and firewall-protected;
- named Docker volumes must be preserved across ordinary shutdown/restart;
- initial ClamAV signature population may delay health for several minutes and must not be bypassed;
- `npx supabase` is the supported CLI invocation; no global Supabase binary is required;
- application objects always use private MinIO. Supabase Storage and its S3 protocol remain disabled;
- Studio is optional local operator tooling only. Enabling it does not make it an application dependency or authorize network exposure.

For a fresh Mint reconstruction, verify Docker/Compose, Node/npm, Python, Git, and `npx supabase --version` before bootstrap. A distribution upgrade, Docker data-root move, firewall change, or checkout relocation requires rerunning the complete validation section below.

## Bootstrap

From the repository root on Linux:

```bash
cp .env.example .env
${EDITOR:-vi} .env
npx supabase --version
(umask 077 && test -e supabase/signing_keys.json || printf '[]\n' > supabase/signing_keys.json)
npx supabase gen signing-key --algorithm ES256
npx supabase start
npx supabase status
docker compose config --quiet
docker compose up -d db minio minio-init clamav
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic current --check-heads
docker compose up --build -d api web
```

CLI 2.109.1 is verified through `npx`; no global `supabase` binary is required or currently available. This CLI reads a configured signing-key file before first generation, so the guarded command creates a mode-`0600`, non-secret empty JSON array only when ignored `supabase/signing_keys.json` is absent. The exact `npx supabase gen signing-key --algorithm ES256` command then writes the private key there. Never display, copy, stage, or commit that file. Replace every `.env` `change-me` value, then manually copy only the browser-safe local anon key line from `npx supabase status` to `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Do not copy service-role, secret, JWT-secret, or signing-key values into browser-visible variables. The API reaches local Supabase JWKS through the Linux `host.docker.internal` gateway while validating the loopback issuer embedded in tokens.

The Supabase CLI database on port `54322` is internal to Auth and remains separate from application PostgreSQL on Compose service `db`/host port `5432`. The tracked Auth stack enables email confirmation and local Mailpit capture, exact loopback callbacks, ES256 signing, and TOTP enrollment/verification. Supabase Studio may be enabled only for local operator use. Supabase Storage and its S3 protocol, Analytics, Edge Runtime/functions, Realtime, and vector services remain disabled. The `[api]` switch stays enabled because CLI 2.109.1 otherwise removes the gateway that exposes the browser-facing Auth route.

The one-shot `minio-init` service waits for healthy MinIO, creates `MINIO_BUCKET` with `--ignore-existing`, and enforces anonymous access `none`. MinIO API CORS is configured directly on the server with `MINIO_API_CORS_ALLOW_ORIGIN=http://localhost:3000`; no bucket CORS XML or unsupported `mc cors set` step is used. ClamAV persists signatures in `keeper_clamav` at `/var/lib/clamav`; a new volume may require several minutes for initial definitions. Its healthcheck sends a real clamd `PING` and requires `PONG`. The API waits for healthy PostgreSQL, MinIO, and ClamAV plus successful bucket initialization. No service runs Alembic automatically: migration remains a deliberate operator command after infrastructure health and before normal application startup.

## Validation

```bash
docker compose ps --all
docker compose run --rm api alembic current --check-heads
docker compose run --rm api alembic check
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/health/db
curl --fail http://localhost:9000/minio/health/live
.venv/bin/python apps/api/scripts/verify_clamav.py --host 127.0.0.1 --port 3310
docker compose logs --tail=100 db minio minio-init clamav api web
npx supabase status
curl --fail http://127.0.0.1:54321/auth/v1/health
curl --fail http://127.0.0.1:54321/auth/v1/.well-known/jwks.json
curl --fail http://127.0.0.1:54323/
curl --fail http://127.0.0.1:54324/
curl --fail http://localhost:3000/
```

The Studio probe applies only when Studio is intentionally enabled for the local operator. The Mailpit probe confirms local capture UI reachability, not external delivery. The tracked `supabase/config.toml` must continue to set `[storage].enabled = false` and `[storage.s3_protocol].enabled = false`. Do not enable Supabase Storage or its S3 protocol to satisfy an application-storage check. MinIO remains the only approved application object store.

Historical live evidence on 2026-07-16: `clamav/clamav:stable` pulled at digest `sha256:7f5389ccaa2368c383fa80e167ccfe44348d71e685f926fce4755eed1757673a`; a fresh persistent signature volume reached real PING/PONG health in 45 seconds. The rebuilt API imported libmagic/Pillow/pypdf, resolved fail-closed `clamav:3310`, stayed healthy with zero restarts, reached PostgreSQL, and reported the then-current migration head `20260717_0005`. PostgreSQL, MinIO, ClamAV, API, and web were running; healthchecked services were healthy. The in-memory verifier returned `clean: OK` and `EICAR: FOUND`. Real-clamd endpoint integration passed for synthetic authenticated candidate/AAL2 PDF, JPEG, and PNG requests. The isolated API run collected 252 tests (251 passed, one PostgreSQL-only skip), all 77 web tests passed, lint/type/build passed, Python/npm audits found no known dependency vulnerabilities after upgrades, and Trivy found no fixable high/critical findings in the API or mandated ClamAV images.

At that 2026-07-16 checkpoint, `alembic check` exited non-zero for Phase 1D model/schema differences. The later merged forward migration `20260718_0007` resolves that drift without rewriting issued history; the source chain now has one head and recorded post-migration `make migrate-check` evidence is clean. The local SMTP service is still mail capture, not real delivery. The Supabase CLI stack is not upstream production-hardened, and its broadly bound ports require host-firewall protection even though the Compose services are loopback-bound.

The expected container database connection is `postgresql+psycopg://<user>:<password>@db:5432/<database>`; `localhost` would address the API container itself and is rejected in production configuration. Compose API-to-MinIO requests use `http://minio:9000` and Compose scanning uses `clamav:3310`. `make api-dev` runs `apps/api/scripts/run_local_api.py`, which loads the ignored local values, maps the approved MinIO credentials/bucket into the host S3 adapter without printing them, and uses `http://127.0.0.1:9000` plus `127.0.0.1:3310`. Short-lived browser download endpoints remain loopback. Path-style S3 addressing is forced. Do not start a host API with the Compose-only `minio` or `clamav` DNS names.

To validate the tracked Compose mechanism without reading a real `.env` or emitting environment values:

```bash
KEEPER_ENV_FILE=.env.example docker compose --env-file .env.example config --quiet
```

For source checks, run `make bootstrap` once and then:

```bash
make lint
make typecheck
make test
make build
git diff --check
```

## Authentication and authorization

Supabase proves identity only. Ordinary portal access still needs an active verified local `UserIdentity`, application role, and permitted relationship/lifecycle state. The one deliberate exception is the validated posting-bound application-start operation: after JWT validation it confirms the exact bearer identity and `email_confirmed_at` against local Supabase Auth `/user`, then atomically creates or reuses the narrow candidate mapping and posting-specific attempt. It does not require those rows before creating them. Generic sign-in remains non-provisioning. Production disables development identity headers and requires AAL2 for administrators. The seed script creates no Supabase users.

### Safe manual candidate and onboarding journey

Seeded local `User`, `UserIdentity`, candidate, admin, posting, plan, and related application rows are fixtures only. The seed also idempotently configures the ungranted `agent` role definition required by explicit onboarding completion; it does not grant agent access. Seeded users are not automatically real Supabase login identities, and matching a seeded email address does not safely link the records. Do not create an Auth user with a seeded email, edit Auth/application tables in Studio, or hand-link subjects merely to make a manual test pass.

Use this procedure only with synthetic local data and the loopback-only stack:

1. Start the tracked Supabase and application services, apply the issued migrations, load the documented local synthetic fixtures, and confirm Auth health, Mailpit, API health, and the published synthetic posting. Do not use a real applicant's email or data.
2. Open the published synthetic opportunity from `http://localhost:3000/careers`. Start there rather than navigating directly to a generic Auth URL so the validated posting context is present.
3. Register a new unique Supabase account, for example an operator-controlled `+candidate-<timestamp>` address accepted by local Mailpit. Use a password created only for this disposable local identity. Do not reuse a seeded fixture email or a real production credential.
4. Open the confirmation message only in local Mailpit and follow its loopback callback. Record whether the callback returns to the selected posting-specific application and whether a subsequent fresh browser request retains candidate access. Never copy access/refresh tokens, callback codes, cookies, or confirmation URLs into reports or logs.
5. Return to the published posting with the confirmed account and select **Sign in with an existing account**. The URL must contain only that published posting slug, successful sign-in must reuse the same application attempt, and a fresh browser request must retain access. Generic `/auth/sign-in` remains a separate non-provisioning path.
6. To prove the recovery boundary, create a second unique synthetic Auth identity, confirm it through Mailpit without a posting context, verify generic candidate access is denied, then return to the published posting and use its existing-user sign-in action. The posting-bound start must create the narrow local mapping exactly once. Do not create or edit application mappings manually.
7. Exercise refresh, expiry/revocation, and a new browser request. A valid refresh must preserve the mapped session; invalid or revoked sessions must return to sign-in without provisioning or leaking credentials.

### Safe local administrator identity link and AAL2 procedure

Seeded application identities are fixtures. The only approved bridge for the
synthetic seeded administrator is the local-only script below. It replaces only
the known seeded placeholder subject and refuses a genuine existing subject,
duplicate subject, inactive user, or missing admin role. It never grants a
role, creates a Supabase Auth user, uses service-role credentials, or links an
identity merely because email addresses match.

1. Confirm the loopback-only Supabase stack and application services are healthy and that the local application fixtures have been seeded with `make seed`. The seed wrapper runs inside the API container so it uses the same Docker database URL and `/run/secrets` borrower key mounts as the running API. Open local Studio at `http://127.0.0.1:54323` from the continuation host only.
2. In **Authentication → Users**, create the synthetic Auth user `admin@example.test` with an operator-controlled local-only password and **Auto Confirm User** enabled. Do not use a real person's email or credential.
3. Open that Auth user and copy only its **User UID**. Do not copy a token, cookie, provider payload, confirmation link, service-role key, JWT secret, or password.
4. If `admin@example.test` was previously linked to the wrong local Auth UID, reset only that synthetic administrator mapping back to the seeded placeholder. This is a local-only operator recovery command; it does not grant roles, create users, or affect any other identity:

   ```bash
   make reset-local-admin
   ```

5. From the repository root, pass the current local Auth user UUID explicitly to the supported Docker wrapper. It runs inside the API container so the command uses the same Compose database URL and `/run/secrets` borrower key mounts as the running API. Do not store the UUID in `.env` or source control:

   ```bash
   make link-local-admin SUPABASE_SUBJECT='<SUPABASE_USER_UUID>'
   ```

   The expected bounded result is either `The local administrator identity was linked successfully.` or the idempotent `The local administrator identity is already linked.` Any refusal is a stop condition; do not edit application or Auth tables by hand.

6. Open `http://localhost:3000/auth/sign-in?returnTo=/admin` and sign in as the synthetic Auth user. The return path supplies navigation intent only and cannot grant application authorization.
7. Continue at `/auth/mfa?returnTo=/admin`. Select **Begin TOTP enrollment**, scan the displayed QR code (or privately enter its one-time setup key), enter the current six-digit code, and select **Verify authenticator**. Do not put the setup key or codes in logs, screenshots, shell history, or reports.
8. Select **Continue to administration**. Loading `/admin` invokes `GET /api/v1/auth/access?area=admin` server-side; reaching the authorized shell proves that the access probe returned success for the current AAL2 session. To retain bounded operational evidence without exporting a token, run `docker compose logs --since=2m api` and confirm the access request completed with status `200`. Do not enable verbose authorization-header logging. A denial must return to sign-in or MFA and must not be bypassed.
9. Open `http://localhost:3000/admin/candidates` and `http://localhost:3000/admin/onboarding`. Both routes repeat server/API authorization; navigation visibility alone is not evidence of access.

No shell command can safely reproduce the browser's cookie-bound TOTP session
without exporting an access token, so the supported access check is the exact
browser navigation above. Never paste a bearer token into shell history merely
to call `/api/v1/auth/access?area=admin` with `curl`.

### Local Documenso TLS integration

Keeper keeps the approved public signing origin at
`https://sign.keeperfinancial.ca` and does not weaken HTTPS, redirect, template,
recipient, provenance, or provider-status validation for local development.
The local Documenso stack must be running from `/home/john/dev/documenso` so its
`documenso_default` Docker network exists. Its public URL settings must use the
same exact HTTPS origin; its private internal URL may remain container-local.

Generate one ignored local CA, server certificate, and combined API trust bundle
from the repository root. The script refuses to overwrite existing material so
an already trusted local CA is not silently replaced:

```bash
./infrastructure/documenso/generate-local-tls.sh
```

Add the exact hostname to the continuation host using an interactive
administrator shell. Do not bind the proxy to a non-loopback interface:

```bash
printf '127.0.0.1 sign.keeperfinancial.ca\n' | sudo tee -a /etc/hosts
```

In Firefox, open **Settings → Privacy & Security → Certificates → View
Certificates → Authorities → Import**, select
`storage/local-documenso-tls/ca.crt`, and trust it only to identify websites.
The CA private key and all generated TLS material remain under the ignored
`storage/local-documenso-tls/` directory and must never be committed or shared.

Start the loopback-only TLS proxy and recreate the API so it receives the exact
provider URL and combined CA bundle:

```bash
docker compose up -d documenso-tls api
```

Verify TLS without printing the API token or provider response body:

```bash
curl --resolve sign.keeperfinancial.ca:443:127.0.0.1 \
  --cacert storage/local-documenso-tls/ca.crt \
  --output /dev/null --write-out '%{http_code} %{ssl_verify_result}\n' \
  https://sign.keeperfinancial.ca/
```

An HTTP redirect with TLS verification result `0` is acceptable for the root
page. Agreement issuance must still be performed through the authenticated
administrator/AAL2 operation. A failed read-only template preflight or any
incompatible issuance response remains a stop condition; do not bypass it with
a manual envelope link.

Before assigning onboarding, the selected application attempt—not merely another application for the same candidate—must have completed the approved review transitions and be `conditionally_selected`; the onboarding plan must exist and be active. Use only supported admin operations to assign the plan, then verify that candidate and admin onboarding are discoverable in their navigation, the candidate sees only assignment-bound tasks/documents, and acknowledgement rejects any version not assigned through that active assignment. Satisfying all gates may produce `activation_ready=true`; it does not perform final activation.

The repository also provides opt-in local-stack checks. They use only unique
synthetic identities and do not print tokens, cookies, callback codes, or
provider payloads:

```bash
cd apps/web
KEEPER_RUN_LOCAL_AUTH_E2E=1 \
KEEPER_LOCAL_E2E_POSTING=test-recruitment-posting-01 \
node --env-file=../../.env ../../node_modules/vitest/vitest.mjs run \
  tests/local-candidate-auth-journey.integration.test.ts

cd ../..
KEEPER_LOCAL_SUPABASE_ACCESS_TOKEN='<synthetic-local-token>' .venv/bin/pytest apps/api/tests/test_supabase_jwt_verification.py
```

The first command additionally requires the documented local public API/Auth/
Mailpit endpoints, local anon key, and a published synthetic posting. The
second enables only the genuine JWT/JWKS/Auth-user verification case; without
its explicit token the live test skips. Never put the token in `.env`, source
control, or test output. The anon key is browser-safe, but it must not be
confused with or replaced by a service-role credential.

Local source-level/API tests may still use `APP_ENV=local`, local filesystem fixtures, `MALWARE_SCANNER_BACKEND=local_test`, and documented development headers. Those are not live Compose settings. The live stack uses MinIO and `MALWARE_SCANNER_BACKEND=clamav`; production startup rejects `local_test` and `disabled`. Scanner connection, timeout, protocol, or daemon failures return safe 503 responses and never fall back to accepting or storing bytes.

## Safe ClamAV verification

Wait for `docker compose ps clamav` to report healthy, then run:

```bash
.venv/bin/python apps/api/scripts/verify_clamav.py --host 127.0.0.1 --port 3310
```

The script keeps both samples in memory, uses clamd `INSTREAM`, prints only `clean: OK` and `EICAR: FOUND`, and exits nonzero on any mismatch. It assembles the standard test marker from split fragments at runtime and never writes it to disk. Do not replace this flow with a downloaded script, disable host antivirus, or create a marker file. The authenticated endpoint is `/api/v1/upload-document`; source-level integration tests use the established synthetic candidate/AAL2 strategy, while live verification must use a genuine existing candidate session rather than fabricating production identity.

## Database changes

Create new Alembic revisions under `apps/api/alembic/versions`; never rewrite a revision already applied to the live database. Apply and inspect from the built API image:

```bash
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic current --check-heads
docker compose run --rm api alembic check
```

The API image working directory is `/app/apps/api`, matching `alembic.ini` and its relative `alembic` script path.

## Shutdown and Docker permission troubleshooting

```bash
docker compose down
npx supabase stop
```

Named PostgreSQL and MinIO volumes are retained. Do not use `docker compose down --volumes` unless destructive data deletion is explicitly intended.

If the daemon reports permission denied for `/var/run/docker.sock`, the requested one-line immediate activation is:

```bash
sudo usermod -aG docker "$USER" && newgrp docker
```

This repository does not run that command. A full logout and login after `usermod` is the cleaner persistent activation for all new sessions.

## Candidate browser-completion verification

A new candidate without an assignment must load `/candidate/application`
without polling the full onboarding dashboard. Onboarding must be absent from
the shared navigation; directly opening `/candidate/onboarding` must show the
stable “not available yet” state. The application form must display the
100-character interest minimum, `YYYY-MM` month controls, and conditional
referral-detail rule before save.

From the exact application document section, use **Set up MFA to access
documents** when no verified factor exists or **Verify with MFA to access
documents** for an AAL1 session with a verified factor. Complete the local TOTP
ceremony and confirm return to `/candidate/applications/{application_id}#documents`.
The refreshed session must be AAL2, document ownership remains enforced by the
API, and the candidate must still be denied from `/admin`.

At AAL2, existing document metadata loads automatically. Confirm a visible
list or **No documents uploaded yet**, rather than a disappearing load button.
A clean synthetic PDF/DOC/DOCX upload must announce success, refresh safe
metadata, preserve category, and reset only the file input. A scanner outage
and storage outage must remain distinct safe `503` failures with no false
success or document metadata. For host-run API validation, start with
`make api-dev`; for Compose, retain the explicit internal service endpoints.

For format validation, use only synthetic documents. The declared MIME must be
the approved exact format MIME. A DOCX that libmagic reports as a ZIP-family
type is accepted only after its bounded OPC/WordprocessingML structure is
proved. The UI must map the safe type/structure/size/malware/scanner/storage
categories without displaying parser output. The opt-in local journey accepts
temporary synthetic standard-PDF and standard-DOCX paths through
`KEEPER_LOCAL_E2E_PDF_PATH` and `KEEPER_LOCAL_E2E_DOCX_PATH`; keep those
process-only and do not add them to `.env`. When both paths and the Firefox BiDi
session endpoint are supplied, the journey uses the real file controls, TOTP,
ClamAV, MinIO, list refresh, and safe invalid-file rejection.

For draft feedback, scroll the action area into view and save a valid draft.
The nearby polite status and button must progress through saving to saved
without changing the visible scroll position or stranding focus. The section
outline is informational normal-flow content and must not cover headings.

At normal 100% zoom, inspect `/` at 320, 375, 768, 1024, 1280, 1366, 1536,
and 1920 CSS pixels. `documentElement.scrollWidth` must not exceed the viewport;
header, hero, trust strip, and following content must share coherent centering,
and the intended hero subjects must remain visible.

For the corresponding administrator check, select the exact submitted
opportunity and attempt in `/admin/candidates`, choose **Begin review**, then
send the bounded information request. The action is intentionally disabled
while the attempt is merely `application_submitted`; it is permitted only in
`under_review` or `interview`. Confirm the chosen application moves to
`more_information_required`, another attempt is unchanged, and the candidate
status view contains only the bounded request message—not interview notes.
