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
