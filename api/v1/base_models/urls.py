from django.urls import path, include

app_name = 'base_models'

urlpatterns = [
    path('organization/', include('api.v1.base_models.organization.urls')),
    path('user/', include('api.v1.base_models.user.urls')),
    path('', include('api.v1.base_models.common.currency.urls')),
] 