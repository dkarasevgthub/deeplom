include .env
export

export PROJECT_ROOT=$(CURDIR)

db-up:
	docker compose up -d postgres-db

db-down:
	docker compose down postgres-db

db-reset:
	make db-down
	if exist out\pgdata rmdir /S /Q out\pgdata

migrate-create:
	docker compose run --rm db-migrate \
		create \
		-ext sql \
		-dir /migrations \
		-seq "$(name)"

migrate-up:
	make migrate-action action=up

migrate-down:
	make migrate-action action=down

migrate-action:
	docker compose run --rm db-migrate \
		-path /migrations \
		-database postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-db:5432/${POSTGRES_DB}?sslmode=disable \
		"${action}"

db-port-forward:
	docker compose up -d port-forwarder

db-port-close:
	docker compose down port-forwarder