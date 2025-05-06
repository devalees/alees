from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyProfileView, UserViewSet

app_name = 'user'

# Create a router and register the UserViewSet
router = DefaultRouter()
router.register('', UserViewSet, basename='user')

urlpatterns = [
    path('profiles/me/', MyProfileView.as_view(), name='my-profile'),
    path('', include(router.urls)),
] 