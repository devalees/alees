"""
URL routing for product endpoints.
"""
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ProductViewSet

# Create a router and register the viewsets
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

# URLPatterns
urlpatterns = [
    path('', include(router.urls)),
] 