# Use a slim Python base image
FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Prevent prompts during apt-get install
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
# Includes build tools, postgres client, libs for psycopg2 (if not binary),
# Pillow (libjpeg, zlib), lxml (libxml2, libxslt1), and netcat for entrypoint
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    # Added for Pillow
    libjpeg-dev \
    zlib1g-dev \
    # Added for potential lxml/xlsx dependencies
    libxml2-dev \
    libxslt1-dev \
    # Clean up apt cache
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group 'app'
# Create application directory and set ownership
RUN useradd -m -s /bin/bash app && \
    mkdir -p /app && \
    chown -R app:app /app

# Set the working directory
WORKDIR /app

# Copy requirements files first to leverage Docker cache
COPY --chown=app:app requirements/ /app/requirements/

# Install Python dependencies
# Includes base, dev (for debug toolbar etc.), and test (for the test service)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/base.txt && \
    pip install --no-cache-dir -r requirements/test.txt

# Copy the entrypoint script and make it executable
COPY --chown=app:app entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create coverage directory and file with correct permissions
# Removed chmod 777 - rely on user ownership
RUN mkdir -p /app/coverage && \
    touch /app/.coverage && \
    chown -R app:app /app/coverage /app/.coverage

# Copy the rest of the application code
# Ensure you have a .dockerignore file in your project root!
COPY --chown=app:app . .

# Switch to the non-root user
USER app

# Set the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command to run (can be overridden in docker-compose.yml)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]