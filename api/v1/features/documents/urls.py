from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet

# Create a router and register our viewset
router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

# URLs will be:
# - /api/v1/documents/ - List all documents
# - /api/v1/documents/{id}/ - Retrieve, update, delete a document

urlpatterns = [
    path('', include(router.urls)),
] 