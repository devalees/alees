from django.urls import path, include # Ensure path and include are imported
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView # Import simplejwt view

# Import ViewSets/Views from sub-apps
from .uom.views import UomTypeViewSet, UnitOfMeasureViewSet
from .status.views import StatusViewSet
from .currency.views import CurrencyViewSet
# Import Auth views
from .auth.views import (
    CustomTokenObtainPairView,
    TOTPSetupView,
    TOTPVerifyView,
    TOTPDisableView,
    PasswordChangeView
)
from .fileStorage.views import FileStorageViewSet, FileUploadView # Import FileStorage views
# from .address.views import AddressViewSet # Commented out
# Import other common viewsets...

app_name = 'common'

# --- Router Configuration --- 
router = DefaultRouter()

# Register UoM ViewSets
router.register(r'uom-types', UomTypeViewSet, basename='uomtype')
router.register(r'uoms', UnitOfMeasureViewSet, basename='unitofmeasure')

# Register Status ViewSet
router.register(r'statuses', StatusViewSet, basename='status')

# Register Currency ViewSet
router.register(r'currencies', CurrencyViewSet, basename='currency')

# Register FileStorage ViewSet (Note the combined prefix)
router.register(r'file-storage/files', FileStorageViewSet, basename='file') 

# Register other common ViewSets (Commented out)
# router.register(r'addresses', AddressViewSet, basename='address')


# --- urlpatterns --- 
# Define specific paths BEFORE the router include
urlpatterns = [
    # Specific FileStorage Upload URL
    path('file-storage/files/upload/', FileUploadView.as_view(), name='file-upload'),
    
    # Specific Auth URLs
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/2fa/totp/setup/', TOTPSetupView.as_view(), name='2fa-totp-setup'),
    path('auth/2fa/totp/verify/', TOTPVerifyView.as_view(), name='2fa-totp-verify'),
    path('auth/2fa/totp/disable/', TOTPDisableView.as_view(), name='2fa-totp-disable'),
    path('auth/password/change/', PasswordChangeView.as_view(), name='password-change'),
]

# Add router URLs AFTER specific paths
urlpatterns += router.urls

# Ensure no leftover includes for deleted urls.py files

# Example of potentially including other sub-app urls if they existed
# urlpatterns += [
#     path('statuses/', include('api.v1.base_models.common.status.urls')),
# ]

# Add other common app URLs here if any
# urlpatterns += [
#     # Include URLs from the status sub-app
#     path('', include('api.v1.base_models.common.status.urls')),
# ] 