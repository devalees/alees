from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import FileUploadView, FileStorageViewSet # Import ViewSet

app_name = 'file_storage'

router = DefaultRouter()
router.register(r'files', FileStorageViewSet, basename='file') # Register ViewSet

urlpatterns = [
    path('files/upload/', FileUploadView.as_view(), name='file-upload'),
    path('', include(router.urls)), # Include router urls
]
