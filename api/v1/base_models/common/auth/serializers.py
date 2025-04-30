from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework import serializers
from django_otp.plugins.otp_totp.models import TOTPDevice

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for obtaining JWT token pair.
    Extends the default TokenObtainPairSerializer to allow for future customization.
    """
    pass

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Custom serializer for refreshing JWT token.
    Extends the default TokenRefreshSerializer to allow for future customization.
    """
    pass

class TOTPVerifySerializer(serializers.Serializer):
    token = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        request = self.context['request']
        try:
            device = TOTPDevice.objects.get(user=request.user, confirmed=False)
        except TOTPDevice.DoesNotExist:
            raise serializers.ValidationError("No unconfirmed TOTP device found.")
        
        if not device.verify_token(attrs['token']):
            raise serializers.ValidationError("Invalid token.")
        
        attrs['device'] = device
        return attrs
