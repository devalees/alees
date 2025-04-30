from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import TOTPSetupView, TOTPVerifyView, UserProfileView

app_name = 'auth'

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('2fa/setup/', TOTPSetupView.as_view(), name='totp-setup'),
    path('2fa/verify/', TOTPVerifyView.as_view(), name='totp-verify'),
    path('user-profile/', UserProfileView.as_view(), name='user-profile'),
]
