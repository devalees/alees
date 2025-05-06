"""
Products app configuration.
"""
from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """Configuration for Products app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.v1.features.products'
    verbose_name = 'Products' 