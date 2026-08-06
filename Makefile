SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

.PHONY: help init check config build test frontend-build up down restart ps logs wait api-smoke frontend-smoke migrate migration-smoke migration-cycle auth-smoke clean reset

help:
	@printf '%s\n' \
	  'Mail Attachment Hub development commands' \
	  '' \
	  '  make init       Create .env with generated secrets' \
	  '  make check      Run static repository checks' \
	  '  make config     Render and validate Docker Compose config' \
	  '  make build      Build backend and frontend images' \
	  '  make test       Run backend tests in Docker' \
	  '  make up         Start backend, PostgreSQL and Redis' \
	  '  make wait       Wait until all services are healthy' \
	  '  make api-smoke  Verify live and ready API endpoints' \
	  '  make migrate    Apply all database migrations' \
	  '  make migration-smoke Verify current schema revision' \
	  '  make migration-cycle Test downgrade and upgrade' \
	  '  make auth-smoke Verify admin login and protected endpoint' \
	  '  make frontend-smoke Verify the web UI and reverse proxy' \
	  '  make ps         Show service status' \
	  '  make logs       Follow service logs' \
	  '  make down       Stop services' \
	  '  make reset      Delete containers and persistent volumes'

init:
	@./scripts/init-env.sh

check:
	@./tests/repository-check.sh
	@./tests/clean-tree-check.sh
	@./tests/env-check.sh .env.example
	@./tests/compose-static-check.sh
	@./tests/backend-static-check.sh
	@./tests/migration-static-check.sh
	@./tests/frontend-static-check.sh

config:
	@./scripts/require-env.sh
	@docker compose --env-file .env -f compose.yml config --quiet

build: config
	@docker compose --env-file .env -f compose.yml build backend frontend

frontend-build: config
	@docker compose --env-file .env -f compose.yml build frontend

test: build
	@docker compose --env-file .env -f compose.yml run --rm --no-deps \
	  --entrypoint sh backend -c "pip install --no-cache-dir '.[test]' >/dev/null && pytest"

up: config
	@docker compose --env-file .env -f compose.yml up -d --build
	@$(MAKE) wait

wait:
	@./scripts/wait-for-services.sh

api-smoke:
	@./scripts/api-smoke.sh

migrate:
	@docker compose --env-file .env -f compose.yml exec -T backend alembic upgrade head

migration-smoke:
	@./scripts/migration-smoke.sh

migration-cycle:
	@./scripts/migration-cycle.sh

auth-smoke:
	@./scripts/auth-smoke.sh

frontend-smoke:
	@./scripts/frontend-smoke.sh

down:
	@docker compose --env-file .env -f compose.yml down

restart:
	@docker compose --env-file .env -f compose.yml restart

ps:
	@docker compose --env-file .env -f compose.yml ps

logs:
	@docker compose --env-file .env -f compose.yml logs -f --tail=100

clean:
	@docker compose --env-file .env -f compose.yml down --remove-orphans

reset:
	@docker compose --env-file .env -f compose.yml down --volumes --remove-orphans
