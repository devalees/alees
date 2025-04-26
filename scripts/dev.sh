#!/bin/bash

# Function to display help
show_help() {
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  up          - Start all services"
    echo "  down        - Stop all services"
    echo "  build       - Build Docker images"
    echo "  logs        - Show logs for all services"
    echo "  shell       - Open a shell in the API container"
    echo "  migrate     - Run database migrations"
    echo "  createsuperuser - Create a Django superuser"
    echo "  test        - Run tests"
    echo "  help        - Show this help message"
}

# Function to start services
start_services() {
    docker-compose up -d
}

# Function to stop services
stop_services() {
    docker-compose down
}

# Function to build images
build_images() {
    docker-compose build
}

# Function to show logs
show_logs() {
    docker-compose logs -f
}

# Function to open shell
open_shell() {
    docker-compose exec api bash
}

# Function to run migrations
run_migrations() {
    docker-compose exec api python manage.py migrate
}

# Function to create superuser
create_superuser() {
    docker-compose exec api python manage.py createsuperuser
}

# Function to run tests
run_tests() {
    docker-compose exec api pytest
}

# Main script logic
case "$1" in
    up)
        start_services
        ;;
    down)
        stop_services
        ;;
    build)
        build_images
        ;;
    logs)
        show_logs
        ;;
    shell)
        open_shell
        ;;
    migrate)
        run_migrations
        ;;
    createsuperuser)
        create_superuser
        ;;
    test)
        run_tests
        ;;
    help|*)
        show_help
        ;;
esac