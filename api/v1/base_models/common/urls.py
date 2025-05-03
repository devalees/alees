from django.urls import path, include # Ensure path and include are imported
from rest_framework.routers import DefaultRouter

# Import ViewSets from sub-apps
from .uom.views import UomTypeViewSet, UnitOfMeasureViewSet
# from .address.views import AddressViewSet # Commented out - Implement/uncomment when Address API exists
# from .currency.views import CurrencyViewSet # Commented out - Implement/uncomment when Currency API exists
# from .status.views import StatusViewSet # Commented out - Implement/uncomment when Status API exists
# Import other common viewsets...

app_name = 'common' # Keep the app_name consistent

router = DefaultRouter()

# Register UoM ViewSets
router.register(r'uom-types', UomTypeViewSet, basename='uomtype')
router.register(r'uoms', UnitOfMeasureViewSet, basename='unitofmeasure')

# Register other common ViewSets (Commented out)
# router.register(r'addresses', AddressViewSet, basename='address')
# router.register(r'currencies', CurrencyViewSet, basename='currency')
# router.register(r'statuses', StatusViewSet, basename='status')


# Set urlpatterns directly to the router's generated URLs
urlpatterns = router.urls

# Example of potentially including other sub-app urls if they existed
# urlpatterns += [
#     path('statuses/', include('api.v1.base_models.common.status.urls')),
# ]

# Add other common app URLs here if any
urlpatterns += [
    # Include URLs from the status sub-app
    path('', include('api.v1.base_models.common.status.urls')),
] 