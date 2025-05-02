from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.tests.integration.test_orgscoped_views import ConcreteScopedViewSet

router = DefaultRouter()
router.register(r'test-scoped-items', ConcreteScopedViewSet, basename='test-scoped-item')

urlpatterns = [
    path('', include(router.urls)),
] 