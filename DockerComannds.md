
```markdown
# Docker Development Workflow Commands for Alees Project

This file summarizes common Docker and Docker Compose commands used for developing and managing the Alees project locally. Run these commands from the project's root directory (where `docker-compose.yml` is located).

## Building the Image

These commands build the Docker image based on your `Dockerfile`.

*   **Build or Rebuild Images:**
    ```bash
    docker-compose build
    ```
    *Use this after changing `Dockerfile` or Python requirements (`requirements/*.txt`).*

*   **Force Rebuild (No Cache):**
    ```bash
    docker-compose build --no-cache
    ```
    *Forces a complete rebuild without using Docker's layer cache. Useful if you suspect caching issues.*

*   **Build Specific Service:**
    ```bash
    docker-compose build <service_name>
    ```
    *Example: `docker-compose build api`*

## Starting & Stopping Services

These commands manage the lifecycle of your running containers (api, celery, celery-beat, postgres, redis, test).

*   **Start All Services (Foreground):**
    ```bash
    docker-compose up
    ```
    *Starts all services defined in `docker-compose.yml`. Attaches to logs from all containers in the current terminal. Press `Ctrl+C` to stop.*

*   **Start All Services (Background/Detached):**
    ```bash
    docker-compose up -d
    ```
    *Starts all services in the background. Use `docker-compose logs` to view output.*

*   **Start Specific Services:**
    ```bash
    docker-compose up -d <service_name_1> <service_name_2>
    ```
    *Example: `docker-compose up -d api postgres redis`*

*   **Stop Services:**
    ```bash
    docker-compose stop
    ```
    *Stops running containers without removing them.*

*   **Stop and Remove Containers/Networks:**
    ```bash
    docker-compose down
    ```
    *Stops containers, removes them, and removes the network. **Named volumes (`postgres_data`, `redis_data`) are preserved by default.** This is the standard way to clean up after running `up`.*

*   **Restart Services:**
    ```bash
    docker-compose restart
    ```
    *Restarts all services defined in the compose file.*

*   **Restart Specific Service:**
    ```bash
    docker-compose restart <service_name>
    ```
    *Example: `docker-compose restart api`*

## Viewing Logs

Monitor the output from your containers.

*   **View Logs for All Running Services (Foreground):**
    ```bash
    docker-compose logs -f
    ```
    *Similar to `up` but attaches to already running containers.*

*   **View Logs for a Specific Service:**
    ```bash
    docker-compose logs <service_name>
    ```
    *Shows historical logs. Example: `docker-compose logs celery`*

*   **Follow Logs for a Specific Service (Real-time):**
    ```bash
    docker-compose logs -f <service_name>
    ```
    *Shows logs as they happen. Example: `docker-compose logs -f api`*

*   **View Last N Log Lines for a Service:**
    ```bash
    docker-compose logs --tail=100 <service_name>
    ```
    *Example: `docker-compose logs --tail=50 celery-beat`*

## Running Management Commands

Execute Django `manage.py` commands or other one-off commands inside containers.

*   **Execute Command in a Running Container (`exec`):**
    ```bash
    docker-compose exec <service_name> <command>
    ```
    *Use this to run commands inside a service container that is **already running** (started via `docker-compose up -d`).*
    *   Example (Django Shell): `docker-compose exec api python manage.py shell`
    *   Example (Create Superuser): `docker-compose exec api python manage.py createsuperuser`
    *   Example (Bash Shell): `docker-compose exec api /bin/bash`

*   **Run Command in a New, Temporary Container (`run`):**
    ```bash
    docker-compose run --rm <service_name> <command>
    ```
    *Starts a **new container** for the service, runs the command, and then **removes** the container (`--rm`). Useful for tasks that don't require the main service process to be running, like `makemigrations`.*
    *   Example (Makemigrations): `docker-compose run --rm api python manage.py makemigrations <app_name>`
    *   Example (Check Dependencies): `docker-compose run --rm api pip check`

## Running Tests

Use the dedicated `test` service to run your test suite.

*   **Run All Tests:**
    ```bash
    docker-compose run --rm test
    ```
    *This executes the default `command:` defined for the `test` service in `docker-compose.yml` (which is `pytest ...`). The `--rm` flag removes the test container after tests finish.*

*   **Run Specific Test File/Directory:**
    ```bash
    docker-compose run --rm test pytest path/to/your/test_file.py
    ```

*   **Run Tests with Pytest Arguments:**
    ```bash
    docker-compose run --rm test pytest -k "test_specific_function" -v
    ```

## Cleaning Up Resources

Remove Docker objects associated with the project or globally.

*   **Stop and Remove Containers/Networks (Standard Cleanup):**
    ```bash
    docker-compose down
    ```
    *(As mentioned before, preserves named volumes by default).*

*   **Stop and Remove Containers/Networks AND Volumes:**
    ```bash
    docker-compose down -v
    ```
    ***WARNING: This will delete the data in your `postgres_data` and `redis_data` volumes! Use with caution!***

*   **Prune Unused Docker Volumes:**
    ```bash
    docker volume prune
    ```
    *Removes all named volumes not currently attached to a container.*

*   **Prune Unused Docker Networks:**
    ```bash
    docker network prune
    ```

*   **Prune Unused Docker Images:**
    ```bash
    docker image prune
    ```
    *Removes dangling images (layers with no tagged image pointing to them).*

*   **Prune All Unused Docker Resources (Aggressive):**
    ```bash
    docker system prune -a --volumes
    ```
    ***WARNING: This removes all stopped containers, all networks not used by at least one container, all dangling images, all build cache, AND all unused volumes. Use with extreme caution!***

## Inspecting State

Check the status of Docker objects.

*   **List Project Containers:**
    ```bash
    docker-compose ps
    ```

*   **List All Running Docker Containers:**
    ```bash
    docker ps
    ```

*   **List All Docker Containers (including stopped):**
    ```bash
    docker ps -a
    ```

*   **List Docker Volumes:**
    ```bash
    docker volume ls
    ```

*   **List Docker Networks:**
    ```bash
    docker network ls
    ```

*   **Inspect Container Details:**
    ```bash
    docker inspect <container_id_or_name>
    ```
    *Example: `docker inspect alees_api`*
```

Save this content as `docker_commands.md` in your project root. This should serve as a handy reference for your team.