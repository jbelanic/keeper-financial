.PHONY: bootstrap infra up down compose-config api-install api-dev web-dev lint format typecheck test build migrate migrate-status migrate-check seed openapi

bootstrap: api-install
	npm install

infra:
	docker compose up -d db minio minio-init

up:
	docker compose up --build -d api web

down:
	docker compose down

api-install:
	python3 -m venv .venv
	.venv/bin/pip install -e 'apps/api[dev]'

api-dev:
	.venv/bin/uvicorn keeper_api.main:app --app-dir apps/api/src --reload

web-dev:
	npm run dev --workspace @keeper/web

lint:
	npm run lint
	.venv/bin/ruff check apps/api

format:
	npm run format
	.venv/bin/ruff format apps/api

typecheck:
	npm run typecheck
	.venv/bin/mypy apps/api/src

test:
	npm test
	.venv/bin/pytest apps/api/tests

build:
	npm run build

migrate:
	docker compose run --rm api alembic upgrade head

migrate-status:
	docker compose run --rm api alembic current --check-heads

migrate-check:
	docker compose run --rm api alembic check

compose-config:
	KEEPER_ENV_FILE=.env.example docker compose --env-file .env.example config --quiet

seed:
	APP_ENV=local .venv/bin/python apps/api/scripts/seed_local.py

openapi:
	.venv/bin/python apps/api/scripts/export_openapi.py
	npm run contracts:generate
	npm run format --workspace @keeper/contracts
