from django.urls import path, include

app_name = 'features'

urlpatterns = [
    # Add feature URLs here
    path('', include('api.v1.features.products.urls')),
    path('', include('api.v1.features.documents.urls')),
] 