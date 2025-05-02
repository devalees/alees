"""
This module exists solely to break the circular import between core.models and organization.models.
It provides a way to reference the Organization model without causing import cycles.
"""
from django.apps import apps

def get_organization_model():
    """Get the Organization model from the installed apps."""
    return apps.get_model('api_v1_organization', 'Organization') 