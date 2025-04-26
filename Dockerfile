FROM python:3.10-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Prevents Python from writing pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    # Prevents Python from buffering stdout and stderr
    PYTHONUNBUFFERED=1 \
    # Set timezone
    TZ=UTC

# Create a non-root user
RUN groupadd -r app && useradd -r -g app app

# Set work directory and permissions
WORKDIR /app
RUN chown app:app /app

# Create coverage directory with correct permissions
RUN mkdir -p /app/coverage && chown -R app:app /app/coverage

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat-traditional \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies
COPY --chown=app:app requirements/ /app/requirements/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/base.txt && \
    pip install --no-cache-dir -r requirements/test.txt

# Copy entrypoint script
COPY --chown=app:app entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy project files
COPY --chown=app:app . .

# Switch to non-root user
USER app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
