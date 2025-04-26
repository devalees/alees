from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api_v1_organization'

router = DefaultRouter()
router.register(r'organization-types', views.OrganizationTypeViewSet, basename='organizationtype')

urlpatterns = [
    path('', include(router.urls)),
] 