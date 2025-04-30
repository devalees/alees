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

class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Invalid old password')
        return value

    def validate_new_password(self, value):
        # Add any password validation rules here if needed
        if len(value) < 8:
            raise serializers.ValidationError('Password must be at least 8 characters long')
        return value
