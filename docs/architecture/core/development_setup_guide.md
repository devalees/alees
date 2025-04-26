
# Local Development Environment Setup Guide

## 1. Overview

*   **Purpose**: To provide step-by-step instructions for developers to set up the ERP backend project and its dependencies on their local machine for development and testing.
*   **Goal**: Enable developers to quickly get a working, consistent development environment running that mirrors the core technologies used in staging/production where feasible.
*   **Primary Method**: Utilize **Docker** and **Docker Compose** to manage required services (PostgreSQL, Redis).

## 2. Prerequisites

*   **Git**: Must be installed ([https://git-scm.com/](https://git-scm.com/)).
*   **Docker & Docker Compose**: Must be installed and running ([https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)). Ensure sufficient resources (RAM/CPU) are allocated to Docker Desktop.
*   **Python**: A recent version compatible with the project (e.g., 3.10+) installed locally is helpful for IDE integration and running some commands outside Docker, but primary development often happens *inside* the container.
*   **Code Editor/IDE**: VS Code, PyCharm, etc.
*   **(Optional) `make`:** A `Makefile` can simplify common commands.

## 3. Initial Setup Steps

1.  **Clone Repository:**
    ```bash
    git clone https://github.com/devalees/alees.git
    cd erp_project
    ```
2.  **Environment Configuration (`.env` file):**
    *   Copy the example environment file: `cp .env.example .env`
    *   **Review and Edit `.env`:** Open the `.env` file in your editor.
    *   Fill in necessary values, especially:
        *   `DJANGO_SECRET_KEY`: Generate a new secret key (e.g., using `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`). **Do not use the example key.**
        *   `DATABASE_URL`: Verify it matches the `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `localhost:5432` defined in `docker-compose.yml`.
        *   `REDIS_URL`: Verify it matches the Redis service in `docker-compose.yml` (e.g., `redis://localhost:6379/1` for default cache, `redis://localhost:6379/0` for Celery broker).
        *   Other potential keys for local development (leave blank or use dev defaults if applicable).
    *   **Important:** The `.env` file is ignored by Git (`.gitignore`) and should **never** be committed.
3.  **Build Docker Images:**
    *   Build the necessary Docker images defined in `Dockerfile` and referenced in `docker-compose.yml`.
    *   Command: `docker-compose build`
4.  **Start Services:**
    *   Start the background services (PostgreSQL, Redis) defined in `docker-compose.yml`.
    *   Command: `docker-compose up -d postgres redis` (Replace service names with actual names from your `docker-compose.yml`). Wait a few seconds for them to initialize fully.
5.  **Run Initial Database Migrations:**
    *   Run the Django `migrate` command *inside* the application container to set up the database schema.
    *   Command: `docker-compose run --rm api python manage.py migrate` (Replace `api` with the name of your main Django application service in `docker-compose.yml`).
6.  **Create Superuser (Optional but Recommended):**
    *   Create an initial superuser for accessing the Django Admin interface.
    *   Command: `docker-compose run --rm api python manage.py createsuperuser`
    *   Follow the prompts.
7.  **Load Initial Data (If applicable):**
    *   If there are data migrations or fixtures for essential initial data (like OrganizationTypes, Statuses, Currencies), run the relevant command.
    *   Example: `docker-compose run --rm api python manage.py load_initial_data` (if a custom command exists) or run specific data migrations via `migrate`.
8.  **Start Development Server:**
    *   Start the main Django development server (running inside the container).
    *   Command: `docker-compose up api` (This will run the command specified in the `api` service's `command` or `entrypoint` in `docker-compose.yml`, typically `python manage.py runserver 0.0.0.0:8000`).
    *   Access the application at `http://localhost:8000` (or the mapped port).

## 4. Common Development Tasks

*   **Running Tests:**
    ```bash
    docker-compose run --rm api pytest
    # Or to run tests for a specific app:
    docker-compose run --rm api pytest api/v1/base_models/organization/tests/
    ```
*   **Running `makemigrations`:**
    ```bash
    docker-compose run --rm api python manage.py makemigrations <app_label>
    # Example:
    docker-compose run --rm api python manage.py makemigrations api.v1.base_models.organization
    ```
    *   *Remember to run `migrate` afterwards:* `docker-compose run --rm api python manage.py migrate`
*   **Running `manage.py` commands:**
    ```bash
    docker-compose run --rm api python manage.py <command_name> <args>
    # Example:
    docker-compose run --rm api python manage.py shell_plus
    ```
*   **Running Celery Worker (Manual):**
    ```bash
    # Ensure settings/dev.py has CELERY_TASK_ALWAYS_EAGER = False to test async
    docker-compose run --rm api celery -A config.celery_app worker -l INFO
    ```
*   **Running Celery Beat (Manual):**
    ```bash
    # Ensure settings/dev.py has CELERY_TASK_ALWAYS_EAGER = False
    docker-compose run --rm api celery -A config.celery_app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler # If using DB scheduler
    ```
    *(Note: Running workers/beat manually is common for debugging specific tasks. For general development where async isn't the focus, `ALWAYS_EAGER=True` is simpler).*
*   **Stopping Services:**
    ```bash
    docker-compose down # Stops and removes containers
    # or
    docker-compose stop # Stops containers without removing them
    ```
*   **Accessing Database:** Use a local client (like DBeaver, pgAdmin) connecting to `localhost:5432` (or the mapped port) using the credentials from your `.env` file.
*   **Accessing Redis:** Use `redis-cli` or a GUI client connecting to `localhost:6379` (or the mapped port).

## 5. Troubleshooting Tips

*   Ensure Docker Desktop is running and has sufficient resources.
*   Verify environment variables in `.env` are correct and match `docker-compose.yml` service definitions.
*   If services fail to start, check logs using `docker-compose logs <service_name>`.
*   Run `docker-compose build --no-cache` if you suspect issues with the Docker image build cache.
*   Run `docker-compose down -v` to stop containers and remove associated volumes (use with caution, deletes DB data).

--- END OF FILE development_setup_guide.md ---

How does this look? It covers the essential steps using Docker Compose, which is a very standard and effective way to manage local development environments for projects with multiple services like this one.