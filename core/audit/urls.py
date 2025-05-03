from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'audit' # Namespace for this app's urls

router = DefaultRouter()
router.register(r'audit-logs', views.AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('', include(router.urls)),
] 