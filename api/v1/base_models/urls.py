from django.urls import path, include

urlpatterns = [
    path('organization/', include('api.v1.base_models.organization.urls')),
    path('user/', include('api.v1.base_models.user.urls', namespace='user')),
    path('auth/', include('api.v1.base_models.common.auth.urls', namespace='auth')),
    path('', include('api.v1.base_models.common.currency.urls')),
    path('contact/', include('api.v1.base_models.contact.urls', namespace='contact')),
] 