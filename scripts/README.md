# Management Script Documentation

This document provides detailed information about the available commands in the `manage.sh` script.

## Table of Contents
1. [User Management](#user-management)
2. [Testing](#testing)
3. [Database Management](#database-management)
4. [Development Tools](#development-tools)
5. [System Maintenance](#system-maintenance)
6. [Container Management](#container-management)

## User Management

### Create Superuser
```bash
./manage.sh createsuperuser
```
- Creates a new Django superuser account
- Prompts for username, email, and password
- Required for accessing the Django admin interface

## Testing

### Run All Tests
```bash
./manage.sh test
```
- Runs all pytest tests in the project
- Uses pytest configuration from pytest.ini
- Shows test results and any failures

### Run Tests with Coverage
```bash
./manage.sh test:coverage
```
- Runs all tests with coverage reporting
- Shows which lines of code are covered by tests
- Identifies missing coverage in the codebase

## Database Management

### Apply Migrations
```bash
./manage.sh migrate
```
- Applies all pending database migrations
- Updates database schema to match models
- Safe to run multiple times

### Create New Migrations
```bash
./manage.sh makemigrations
```
- Creates new migration files based on model changes
- Generates migration files in respective app directories
- Review generated files before committing

### Show Migrations
```bash
./manage.sh showmigrations
```
- Lists all migrations and their status
- Shows which migrations have been applied
- Helps track database schema changes

## Development Tools

### Django Shell
```bash
./manage.sh shell
```
- Opens Django's interactive Python shell
- Provides access to all Django models and utilities
- Useful for debugging and data inspection

### Django Shell Plus
```bash
./manage.sh shell_plus
```
- Enhanced Django shell with additional features
- Requires django-extensions package
- Auto-imports common models and utilities

### Check Project
```bash
./manage.sh check
```
- Validates project configuration
- Checks for common problems
- Ensures settings are properly configured

### Show URLs
```bash
./manage.sh show_urls
```
- Lists all URL patterns in the project
- Shows URL patterns and their view functions
- Helps with URL debugging and documentation

## System Maintenance

### Collect Static Files
```bash
./manage.sh collectstatic
```
- Gathers all static files into STATIC_ROOT
- Required for production deployment
- Use --noinput flag for automated deployment

### Clear Cache
```bash
./manage.sh clear_cache
```
- Clears Django's cache
- Useful when cache-related issues occur
- Affects all cache backends

## Container Management

### Restart Containers
```bash
./manage.sh restart
```
- Stops all containers
- Removes all containers
- Starts all containers fresh
- Useful after configuration changes

### View Logs
```bash
./manage.sh logs
```
- Shows real-time container logs
- Follows log output (-f flag)
- Useful for debugging container issues

## Getting Help

### Show Help
```bash
./manage.sh help
```
- Displays this documentation
- Lists all available commands
- Shows command descriptions

## Notes
- All commands must be run from the project root directory
- Docker must be running for all commands to work
- Some commands may require specific packages to be installed
- Commands are executed in the API container by default 