from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Currency
from .serializers import CurrencySerializer

class CurrencyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows currencies to be viewed.
    """
    serializer_class = CurrencySerializer
    permission_classes = [permissions.AllowAny]  # Allow read access to all
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']
    lookup_field = 'code'  # Use code as the primary key for lookups

    def get_queryset(self):
        """
        Return all currencies for detail view, but only active ones for list view
        """
        if self.action == 'list':
            return Currency.objects.filter(is_active=True)
        return Currency.objects.all()

    def list(self, request, *args, **kwargs):
        """
        Override list method to return a list instead of paginated response
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
