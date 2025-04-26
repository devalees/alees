.PHONY: build up down logs ps test test-db migrate createsuperuser shell

build:
	docker-compose build

up:
	docker-compose up -d postgres redis
	sleep 5
	docker-compose up api

down:
	docker-compose down

logs:
	docker-compose logs -f

ps:
	docker-compose ps

# Test database setup and running tests
test-db:
	docker-compose run --rm api python manage.py migrate --settings=config.settings.test

test: test-db
	docker-compose run --rm api pytest --reuse-db

test-cov:
	docker-compose run --rm api pytest --cov=. --cov-report=term-missing --reuse-db

migrate:
	docker-compose run --rm api python manage.py migrate

createsuperuser:
	docker-compose run --rm api python manage.py createsuperuser

shell:
	docker-compose run --rm api python manage.py shell_plus 