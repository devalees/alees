# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.apps import apps # Import apps registry

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.v1.urls', namespace='v1')),
    path('api/core/', include('core.urls', namespace='core')),
]

# Add static and media URLs for development server convenience
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # --- Conditionally import and add debug toolbar urls ---
    try:
        import debug_toolbar
        # Ensure debug_toolbar is in INSTALLED_APPS before including urls
        if 'debug_toolbar' in settings.INSTALLED_APPS:
             urlpatterns = [
                 path('__debug__/', include(debug_toolbar.urls)),
             ] + urlpatterns
    except ImportError:
         # If debug_toolbar is not installed, just pass
         pass
    # --- End Debug Toolbar ---

# --- Add Test App URLs if the app is installed (only during tests) ---
if apps.is_installed('core.tests_app'):
    urlpatterns += [
        path('_test_utils/', include('core.tests_app.urls')),
    ]
# --- End Test App URLs ---