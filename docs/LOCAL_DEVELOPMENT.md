# Local Docker Operations

The local Linux Docker deployment is the live/production target. PostgreSQL (`db`) is the application database, MinIO (`minio`) is the private object store, and the checked-in Supabase CLI configuration supplies Auth because the current browser session and API JWT code requires Supabase semantics. The Supabase stack's internal database remains separate from the application database.

Compose publishes PostgreSQL, MinIO, API, and web ports on loopback only. The Supabase CLI manages its own port bindings; protect them with the Linux host firewall and do not expose any stack service to an untrusted network. [Upstream Supabase documentation](https://supabase.com/docs/guides/local-development/cli-workflows) describes its CLI stack as development-only rather than production-hardened; this is an explicit limitation of the owner-selected local-only model, not an implied security certification.

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
docker compose up -d db minio minio-init
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic current --check-heads
docker compose up --build -d api web
```

CLI 2.109.1 is verified through `npx`; no global `supabase` binary is required or currently available. This CLI reads a configured signing-key file before first generation, so the guarded command creates a mode-`0600`, non-secret empty JSON array only when ignored `supabase/signing_keys.json` is absent. The exact `npx supabase gen signing-key --algorithm ES256` command then writes the private key there. Never display, copy, stage, or commit that file. Replace every `.env` `change-me` value, then manually copy only the browser-safe local anon key line from `npx supabase status` to `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Do not copy service-role, secret, JWT-secret, or signing-key values into browser-visible variables. The API reaches local Supabase JWKS through the Linux `host.docker.internal` gateway while validating the loopback issuer embedded in tokens.

The Supabase CLI database on port `54322` is internal to Auth and remains separate from application PostgreSQL on Compose service `db`/host port `5432`. The tracked Auth stack enables email confirmation and local mail capture, exact loopback callbacks, ES256 signing, and TOTP enrollment/verification. Supabase Storage, Studio, Analytics, Edge Runtime/functions, Realtime, and vector services are disabled. The `[api]` switch stays enabled because CLI 2.109.1 otherwise removes the gateway that exposes the browser-facing Auth route.

The one-shot `minio-init` service waits for healthy MinIO, creates `MINIO_BUCKET` with `--ignore-existing`, and enforces anonymous access `none`. MinIO API CORS is configured directly on the server with `MINIO_API_CORS_ALLOW_ORIGIN=http://localhost:3000`; no bucket CORS XML or unsupported `mc cors set` step is used. The API waits for healthy PostgreSQL and MinIO plus successful bucket initialization. No service runs Alembic automatically: migration remains a deliberate operator command after infrastructure health and before normal application startup.

## Validation

```bash
docker compose ps --all
docker compose run --rm api alembic current --check-heads
docker compose run --rm api alembic check
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/health/db
curl --fail http://localhost:9000/minio/health/live
docker compose logs --tail=100 db minio minio-init api web
npx supabase status
```

Live evidence on 2026-07-16: the tracked `project_id = "keeper-financial"` Supabase configuration started with CLI 2.109.1 after the old `keeper-financial-local` stack was stopped without `--no-backup`; local Auth health succeeds, and JWKS returns HTTP `200` with exactly one ES256 key. Rebuilt/recreated `web` and `api`, PostgreSQL, and corrected immutable MinIO are healthy and loopback-bound; `minio-init` exited `0`; web `/` and `/agents` return success; and API `/health/db` reports reachable. Both `alembic upgrade head` and `alembic current --check-heads` passed at `20260717_0005`. Full clean-environment API pytest and all 77 Vitest tests also passed.

`alembic check` still exits non-zero only because it detects historical Phase 1D model/schema differences in indexes and foreign-key `ondelete`. That command remains a useful diagnostic, but it is not a green acceptance result or a blocker to reaching the checked-in migration head. Historical schema remediation is outside this deployment change. The local SMTP service is mail capture, not real delivery; candidate uploads fail closed while no approved scanner is configured. The Supabase CLI stack is not upstream production-hardened, and its broadly bound ports require host-firewall protection even though the Compose services are loopback-bound.

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

Local source-level/API tests may still use `APP_ENV=local`, local filesystem fixtures, `MALWARE_SCANNER_BACKEND=local_test`, and documented development headers. Those are not live Compose settings. The live stack uses MinIO and `MALWARE_SCANNER_BACKEND=disabled`; candidate file upload therefore fails closed until an approved local scanner exists.

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
