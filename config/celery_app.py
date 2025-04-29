# /config/celery_app.py
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
# This should match how you run your Django app (e.g., read from env or default)
# Using the same default as docker-compose for consistency
os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.dev'))

# Create the Celery application instance
# The first argument is typically the name of your project's main module
app = Celery('config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix in settings.py.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
# This looks for tasks.py files in your INSTALLED_APPS
app.autodiscover_tasks()


# Optional: Example task for testing
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')