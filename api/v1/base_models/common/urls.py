from django.urls import path, include

app_name = 'common' # Define app_name for namespacing if needed

urlpatterns = [
    # Include URLs from the status sub-app
    path('', include('api.v1.base_models.common.status.urls')),
    # Add other common app URLs here if any
] 