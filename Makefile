.PHONY: help setup build up down restart logs logs-bot logs-worker shell-bot shell-worker db-migrate db-revision clean

help:
	@echo "News Relay Bot - Makefile commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup        - Initial setup (create .env, build, migrate)"
	@echo "  make build        - Build Docker images"
	@echo ""
	@echo "Control:"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo ""
	@echo "Logs:"
	@echo "  make logs         - View all logs"
	@echo "  make logs-bot     - View bot logs"
	@echo "  make logs-worker  - View worker logs"
	@echo ""
	@echo "Shell:"
	@echo "  make shell-bot    - Open shell in bot container"
	@echo "  make shell-worker - Open shell in worker container"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate   - Run database migrations"
	@echo "  make db-revision  - Create new migration revision"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove all containers, volumes, and data"

setup:
	@bash setup.sh

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-bot:
	docker-compose logs -f bot

logs-worker:
	docker-compose logs -f worker

shell-bot:
	docker-compose exec bot /bin/bash

shell-worker:
	docker-compose exec worker /bin/bash

db-migrate:
	docker-compose exec bot alembic upgrade head

db-revision:
	@read -p "Enter migration message: " msg; \
	docker-compose exec bot alembic revision --autogenerate -m "$$msg"

clean:
	@echo "⚠️  This will remove all containers, volumes, and data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		rm -rf logs/* media_storage/* .tg_session/*; \
		echo "✅ Cleanup complete"; \
	fi

