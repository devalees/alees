from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

app_name = 'v1'

# Create a router for API endpoints
router = DefaultRouter()

# Include base_models URLs with namespace to properly register nested namespaces
base_models_urls = [
    path('', include('api.v1.base_models.urls', namespace='base_models')),
]

# Include features URLs
features_urls = [
    path('', include('api.v1.features.urls')),
]

urlpatterns = [
    # API Schema documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='v1:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='v1:schema'), name='redoc'),
    
    # API endpoints
    path('', include(base_models_urls)),
    path('', include(features_urls)),
    # path('audit/', include('core.audit.urls', namespace='audit')), # Removed - Handled via core.urls in config/urls.py
] 