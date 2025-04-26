from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Create a router for API endpoints
router = DefaultRouter()

# Include base_models URLs
base_models_urls = [
    path('', include('api.v1.base_models.urls')),
]

# Include features URLs
features_urls = [
    path('', include('api.v1.features.urls')),
]

urlpatterns = [
    # API documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # API endpoints
    path('', include(base_models_urls)),
    path('', include(features_urls)),
] 