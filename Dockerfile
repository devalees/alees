FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/ .
RUN pip install --no-cache-dir -r base.txt && \
    pip install --no-cache-dir -r dev.txt

# Copy project
COPY . .

# Create entrypoint script
RUN echo '#!/bin/bash\n\
python manage.py migrate\n\
python manage.py collectstatic --noinput\n\
exec "$@"' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
