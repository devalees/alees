# Server Management Commands

This document provides a comprehensive list of commands for managing the Django server and related services.

## 1. Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs for all services
docker-compose logs -f

# View logs for a specific service
docker-compose logs -f api  # for Django
docker-compose logs -f postgres  # for PostgreSQL
docker-compose logs -f redis  # for Redis

# Restart a specific service
docker-compose restart api
docker-compose restart postgres
docker-compose restart redis

# Rebuild and restart a service
docker-compose up -d --build api
```

## 2. Django Management Commands

```bash
# Run Django development server
docker-compose exec api python manage.py runserver

# Create a new Django app
docker-compose exec api python manage.py startapp app_name

# Make and apply migrations
docker-compose exec api python manage.py makemigrations
docker-compose exec api python manage.py migrate

# Create a superuser
docker-compose exec api python manage.py createsuperuser

# Collect static files
docker-compose exec api python manage.py collectstatic

# Run tests
docker-compose exec api python manage.py test

# Check project for common problems
docker-compose exec api python manage.py check
```

## 3. Database Commands

```bash
# Access PostgreSQL shell
docker-compose exec postgres psql -U postgres

# Backup database
docker-compose exec postgres pg_dump -U postgres > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres < backup.sql
```

## 4. Redis Commands

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Monitor Redis operations
docker-compose exec redis redis-cli monitor
```

## 5. Celery Commands

```bash
# Start Celery worker
docker-compose exec api celery -A config worker -l info

# Start Celery beat (scheduler)
docker-compose exec api celery -A config beat -l info

# Check Celery status
docker-compose exec api celery -A config status
```

## 6. Development Tools

```bash
# Run flake8 for code linting
docker-compose exec api flake8

# Run black for code formatting
docker-compose exec api black .

# Run isort for import sorting
docker-compose exec api isort .
```

## 7. Monitoring Commands

```bash
# Check service status
docker-compose ps

# View resource usage
docker stats

# Check network connections
docker network ls
```

## 8. Common Workflow Examples

### Starting a new development session:
```bash
# Start all services
docker-compose up -d

# Apply any pending migrations
docker-compose exec api python manage.py migrate

# Create superuser if needed
docker-compose exec api python manage.py createsuperuser
```

### Making changes to the codebase:
```bash
# After making model changes
docker-compose exec api python manage.py makemigrations
docker-compose exec api python manage.py migrate

# After adding new static files
docker-compose exec api python manage.py collectstatic
```

### Troubleshooting:
```bash
# Check logs for errors
docker-compose logs -f api

# Restart services if needed
docker-compose restart api
docker-compose restart postgres
docker-compose restart redis
```

## Notes

- All commands assume you are in the project root directory
- Replace `api` with your service name if different
- Use `-d` flag with `docker-compose up` to run in detached mode
- Use `-f` flag with `docker-compose logs` to follow logs in real-time 