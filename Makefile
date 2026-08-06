SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

.PHONY: help init check config up down restart ps logs wait clean reset

help:
	@printf '%s\n' \
	  'Mail Attachment Hub development commands' \
	  '' \
	  '  make init     Create .env with generated secrets' \
	  '  make check    Run repository and configuration checks' \
	  '  make config   Render and validate Docker Compose config' \
	  '  make up       Start PostgreSQL and Redis' \
	  '  make wait     Wait until both services are healthy' \
	  '  make ps       Show service status' \
	  '  make logs     Follow service logs' \
	  '  make down     Stop services' \
	  '  make reset    Delete containers and persistent volumes'

init:
	@./scripts/init-env.sh

check:
	@./tests/repository-check.sh
	@./tests/clean-tree-check.sh
	@./tests/env-check.sh .env.example
	@./tests/compose-static-check.sh

config:
	@./scripts/require-env.sh
	@docker compose --env-file .env -f compose.yml config --quiet

up: config
	@docker compose --env-file .env -f compose.yml up -d
	@$(MAKE) wait

wait:
	@./scripts/wait-for-services.sh

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
