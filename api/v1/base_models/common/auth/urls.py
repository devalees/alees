from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    TOTPSetupView,
    TOTPVerifyView,
    TOTPDisableView,
    PasswordChangeView
)

app_name = 'auth'

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('2fa/totp/setup/', TOTPSetupView.as_view(), name='2fa-totp-setup'),
    path('2fa/totp/verify/', TOTPVerifyView.as_view(), name='2fa-totp-verify'),
    path('2fa/totp/disable/', TOTPDisableView.as_view(), name='2fa-totp-disable'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
]
