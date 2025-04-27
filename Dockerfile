FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash app && \
    mkdir -p /app && \
    chown -R app:app /app

WORKDIR /app

COPY --chown=app:app requirements/ /app/requirements/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/base.txt && \
    pip install --no-cache-dir -r requirements/test.txt

COPY --chown=app:app entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create coverage directory and file with correct permissions
RUN mkdir -p /app/coverage && \
    touch /app/.coverage && \
    chown -R app:app /app/coverage /app/.coverage && \
    chmod -R 777 /app/coverage /app/.coverage

COPY --chown=app:app . .

USER app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
