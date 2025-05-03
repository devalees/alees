from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from core.audit.models import AuditLog
from .serializers import AuditLogSerializer
from .filters import AuditLogFilter

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows audit logs to be viewed.

    Provides read-only access to AuditLog entries, filterable by various fields.
    Access is restricted to admin users.
    """
    queryset = AuditLog.objects.all().select_related(
        'user', 'organization', 'content_type'
    ).order_by('-created_at') # Use created_at for default ordering
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser] # Only admins can view audit logs

    # Filtering
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AuditLogFilter

    # Ordering
    ordering_fields = [
        'created_at',
        'user__username',
        'organization__name',
        'action_type',
        'content_type__model',
        # 'remote_addr' # Removed as it's not a direct model field
    ]
    ordering = ['-created_at'] # Use created_at for default ordering

    # Pagination will use default settings unless specified otherwise
    # pagination_class = YourCustomPaginationIfNeeded
