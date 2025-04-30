from django.db import models
from rest_framework_api_key.models import AbstractAPIKey

class APIKey(AbstractAPIKey):
    """
    Custom API key model that extends the base API key model.
    This allows for additional fields and customizations if needed.
    """
    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ["-created"]
