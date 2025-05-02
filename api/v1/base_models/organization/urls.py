from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'organization'

router = DefaultRouter()
router.register(r'types', views.OrganizationTypeViewSet, basename='organizationtype')
router.register(r'organization-memberships', views.OrganizationMembershipViewSet, basename='organizationmembership')
router.register(r'', views.OrganizationViewSet, basename='organization')

urlpatterns = [
    path('', include(router.urls)),
]