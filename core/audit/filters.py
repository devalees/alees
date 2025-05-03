import django_filters
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from core.audit.models import AuditLog
from api.v1.base_models.organization.models import Organization # Import Organization model

User = get_user_model()

class AuditLogFilter(django_filters.FilterSet):
    """
    FilterSet for querying AuditLog entries.
    Allows filtering by user, organization, action type, timestamp range,
    content type, and object ID.
    """
    # Timestamp filters for range queries
    created_at_after = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr='gte'
    )
    created_at_before = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr='lte'
    )

    # Filter by related User
    user = django_filters.ModelChoiceFilter(queryset=User.objects.all())

    # Filter by related Organization
    organization = django_filters.ModelChoiceFilter(queryset=Organization.objects.all())

    # Filter by related ContentType
    content_type = django_filters.ModelChoiceFilter(queryset=ContentType.objects.all())

    # Explicit filter for remote_addr (which is stored in context JSON)
    # This requires custom filtering logic if needed, not a direct model field filter.
    # remote_addr = django_filters.CharFilter(lookup_expr='icontains') # Removed as remote_addr not a field

    class Meta:
        model = AuditLog
        fields = {
            'user': ['exact'],
            'organization': ['exact'], # Uncommented to enable filtering
            'action_type': ['exact', 'in'],
            'content_type': ['exact'],
            'object_id': ['exact'],
            # We already defined specific filters for timestamp range
            # and remote_addr isn't a direct field.
        } 