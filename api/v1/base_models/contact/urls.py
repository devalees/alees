from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.v1.base_models.contact.views import ContactViewSet

app_name = 'contact'

router = DefaultRouter()
router.register('contacts', ContactViewSet, basename='contact')

urlpatterns = [
    path('', include(router.urls)),
]
