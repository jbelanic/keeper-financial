# Local Docker Operations

The local Linux Docker deployment is the live/production target. PostgreSQL (`db`) is the application database, MinIO (`minio`) is the private object store, ClamAV (`clamav`) scans documents before persistence, and the checked-in Supabase CLI configuration supplies Auth because the current browser session and API JWT code requires Supabase semantics. The Supabase stack's internal database remains separate from the application database.

Compose publishes PostgreSQL, MinIO, clamd, API, and web ports on loopback only. Clamd TCP has no authentication or encryption, so port 3310 must remain loopback-only. The Supabase CLI manages its own port bindings; protect them with the Linux host firewall and do not expose any stack service to an untrusted network. [Upstream Supabase documentation](https://supabase.com/docs/guides/local-development/cli-workflows) describes its CLI stack as development-only rather than production-hardened; this is an explicit limitation of the owner-selected local-only model, not an implied security certification. [ClamAV's Docker documentation](https://docs.clamav.net/manual/Installing/Docker.html) documents the official image, `/var/lib/clamav` signature database, TCP 3310, and daemon health behavior.

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

The Supabase CLI database on port `54322` is internal to Auth and remains separate from application PostgreSQL on Compose service `db`/host port `5432`. The tracked Auth stack enables email confirmation and local mail capture, exact loopback callbacks, ES256 signing, and TOTP enrollment/verification. Supabase Storage, Studio, Analytics, Edge Runtime/functions, Realtime, and vector services are disabled. The `[api]` switch stays enabled because CLI 2.109.1 otherwise removes the gateway that exposes the browser-facing Auth route.

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
```

Live evidence on 2026-07-16: `clamav/clamav:stable` pulled at digest `sha256:7f5389ccaa2368c383fa80e167ccfe44348d71e685f926fce4755eed1757673a`; a fresh persistent signature volume reached real PING/PONG health in 45 seconds. The rebuilt API imported libmagic/Pillow/pypdf, resolved fail-closed `clamav:3310`, stayed healthy with zero restarts, reached PostgreSQL, and reported migration head `20260717_0005`. PostgreSQL, MinIO, ClamAV, API, and web were running; healthchecked services were healthy. The in-memory verifier returned `clean: OK` and `EICAR: FOUND`. Real-clamd endpoint integration passed for synthetic authenticated candidate/AAL2 PDF, JPEG, and PNG requests. The isolated API run collected 252 tests (251 passed, one PostgreSQL-only skip), all 77 web tests passed, lint/type/build passed, Python/npm audits found no known dependency vulnerabilities after upgrades, and Trivy found no fixable high/critical findings in the API or mandated ClamAV images.

`alembic check` still exits non-zero only because it detects historical Phase 1D model/schema differences in indexes and foreign-key `ondelete`. That command remains a useful diagnostic, but it is not a green acceptance result or a blocker to reaching the checked-in migration head. Historical schema remediation is outside this deployment change. The local SMTP service is mail capture, not real delivery. The Supabase CLI stack is not upstream production-hardened, and its broadly bound ports require host-firewall protection even though the Compose services are loopback-bound.

The expected container database connection is `postgresql+psycopg://<user>:<password>@db:5432/<database>`; `localhost` would address the API container itself and is rejected in production configuration. API-to-MinIO requests use `http://minio:9000`; short-lived browser download redirects use `http://localhost:9000`. Path-style S3 addressing is forced.

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

Supabase proves identity only. An identity still needs an active verified local `UserIdentity`, application role, and permitted relationship/lifecycle state. Production disables development identity headers and requires AAL2 for administrators. The seed script creates no Supabase users.

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
