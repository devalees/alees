from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'organization'

router = DefaultRouter()
router.register(r'types', views.OrganizationTypeViewSet, basename='organizationtype')
router.register(r'', views.OrganizationViewSet, basename='organization')

urlpatterns = router.urls