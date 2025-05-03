from django.urls import path, include

app_name = 'base_models'

urlpatterns = [
    path('organization/', include('api.v1.base_models.organization.urls', namespace='organization')),
    path('user/', include('api.v1.base_models.user.urls', namespace='user')),
    path('contact/', include('api.v1.base_models.contact.urls', namespace='contact')),
    path('common/', include('api.v1.base_models.common.urls', namespace='common')),
] 