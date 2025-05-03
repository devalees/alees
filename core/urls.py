# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import ViewSets from core sub-apps here
from .audit.views import AuditLogViewSet # Import the AuditLogViewSet

app_name = 'core'

router = DefaultRouter()

# Register core ViewSets here
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog') # Register it

urlpatterns = [
    path('', include(router.urls)),
] 