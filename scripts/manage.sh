#!/bin/bash

# Function to display help
show_help() {
    echo "Usage: ./manage.sh [command]"
    echo ""
    echo "Commands:"
    echo "  createsuperuser    Create a Django superuser"
    echo "  test              Run all tests"
    echo "  test:coverage     Run tests with coverage"
    echo "  migrate           Apply database migrations"
    echo "  makemigrations    Create new migrations"
    echo "  shell            Open Django shell"
    echo "  shell_plus       Open Django shell plus"
    echo "  collectstatic    Collect static files"
    echo "  check            Check project for problems"
    echo "  showmigrations   Show all migrations"
    echo "  show_urls        Show all URLs"
    echo "  clear_cache      Clear the cache"
    echo "  restart          Restart all containers"
    echo "  logs             Show container logs"
    echo "  help             Show this help message"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Execute command based on argument
case "$1" in
    createsuperuser)
        docker-compose exec api python manage.py createsuperuser
        ;;
    test)
        docker-compose exec api pytest
        ;;
    test:coverage)
        docker-compose exec api pytest --cov=. --cov-report=term-missing
        ;;
    migrate)
        docker-compose exec api python manage.py migrate
        ;;
    makemigrations)
        docker-compose exec api python manage.py makemigrations
        ;;
    shell)
        docker-compose exec api python manage.py shell
        ;;
    shell_plus)
        docker-compose exec api python manage.py shell_plus
        ;;
    collectstatic)
        docker-compose exec api python manage.py collectstatic --noinput
        ;;
    check)
        docker-compose exec api python manage.py check
        ;;
    showmigrations)
        docker-compose exec api python manage.py showmigrations
        ;;
    show_urls)
        docker-compose exec api python manage.py show_urls
        ;;
    clear_cache)
        docker-compose exec api python manage.py clear_cache
        ;;
    restart)
        docker-compose down && docker-compose up -d
        ;;
    logs)
        docker-compose logs -f
        ;;
    help|*)
        show_help
        ;;
esac 