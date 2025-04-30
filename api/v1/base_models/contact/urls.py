from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.v1.base_models.contact.views import (
    ContactViewSet, ContactEmailAddressViewSet,
    ContactPhoneNumberViewSet, ContactAddressViewSet
)

router = DefaultRouter()
router.register(r'contacts', ContactViewSet)
router.register(r'contact-email-addresses', ContactEmailAddressViewSet)
router.register(r'contact-phone-numbers', ContactPhoneNumberViewSet)
router.register(r'contact-addresses', ContactAddressViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
