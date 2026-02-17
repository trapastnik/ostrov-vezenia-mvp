.PHONY: up down build migrate create-admin logs

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

migrate:
	docker compose exec backend alembic upgrade head

create-migration:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

create-admin:
	docker compose exec backend python -m app.scripts.create_admin

logs:
	docker compose logs -f backend

logs-all:
	docker compose logs -f
