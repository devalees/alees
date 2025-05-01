from django.urls import path, include

from api.v1.base_models.contact.views import ContactViewSet
from api.v1.base_models.contact.routers import CustomRouter

app_name = 'contact'

router = CustomRouter()
router.register('contacts', ContactViewSet, basename='contact')

urlpatterns = [
    path('', include(router.urls)),
]
