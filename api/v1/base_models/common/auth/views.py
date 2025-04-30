from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django_otp.plugins.otp_totp.models import TOTPDevice
from .serializers import TOTPVerifySerializer
from .permissions import IsAuthenticatedOrHasAPIKey
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for obtaining JWT token pair.
    Extends the default TokenObtainPairView to allow for future customization.
    """
    pass

class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom view for refreshing JWT token.
    Extends the default TokenRefreshView to allow for future customization.
    """
    pass

class UserProfileView(APIView):
    """Test view for API Key authentication."""
    permission_classes = [IsAuthenticatedOrHasAPIKey]

    def get(self, request):
        """Return a simple response to test authentication."""
        return Response({"message": "Authenticated successfully"})

class TOTPSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Delete any existing unconfirmed devices
        TOTPDevice.objects.filter(user=request.user, confirmed=False).delete()
        
        # Create new TOTP device
        device = TOTPDevice.objects.create(
            user=request.user,
            name='Default',
            confirmed=False
        )

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        provisioning_uri = device.config_url
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        # Create SVG QR code
        img = qr.make_image(image_factory=qrcode.image.svg.SvgImage)
        stream = BytesIO()
        img.save(stream)
        qr_url = base64.b64encode(stream.getvalue()).decode()

        return Response({
            'secret': device.key,
            'qr_url': qr_url,
            'provisioning_uri': provisioning_uri
        })

class TOTPVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TOTPVerifySerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        device = serializer.validated_data['device']
        device.confirmed = True
        device.save()
        
        return Response({'message': '2FA enabled successfully'}, status=status.HTTP_200_OK)

class TOTPDisableView(APIView):
    """
    View to disable TOTP 2FA for the authenticated user.
    Requires password confirmation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get('password')
        if not password:
            return Response(
                {'error': 'Password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify password
        if not request.user.check_password(password):
            return Response(
                {'error': 'Invalid password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if 2FA is enabled
        if not TOTPDevice.objects.filter(user=request.user, confirmed=True).exists():
            return Response(
                {'error': '2FA is not enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete all TOTP devices for the user
        TOTPDevice.objects.filter(user=request.user).delete()

        return Response(
            {'message': '2FA disabled successfully'},
            status=status.HTTP_200_OK
        )
