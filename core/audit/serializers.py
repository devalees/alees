from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from core.audit.models import AuditLog
# from api.v1.base_models.organization.serializers import OrganizationSummarySerializer # Avoid direct import
from api.v1.base_models.organization.models import Organization # Import model directly

User = get_user_model()

class UserSummarySerializer(serializers.ModelSerializer):
    """Basic user info for audit logs. Allows null users."""
    class Meta:
        model = User
        fields = ('id', 'username', 'email') # Keep it minimal

# Define a simple Org Summary Serializer locally within the audit app
class OrganizationSummarySerializer(serializers.ModelSerializer):
    """Basic organization info for audit logs."""
    class Meta:
        model = Organization
        fields = ('id', 'name')

class ContentTypeSerializer(serializers.ModelSerializer):
    """Serializer for ContentType model."""
    class Meta:
        model = ContentType
        fields = ('id', 'app_label', 'model')

class AuditLogSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for AuditLog entries.
    Provides detailed information about audit events.
    """
    user = UserSummarySerializer(read_only=True, allow_null=True)
    organization = OrganizationSummarySerializer(read_only=True, allow_null=True)
    content_type = ContentTypeSerializer(read_only=True, allow_null=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            'id',
            'created_at',
            # 'updated_at', # Optionally include updated_at if needed
            'user',
            'organization',
            'action_type',
            'action_type_display',
            'content_type',
            'object_id',
            'object_repr',
            'changes',
            'context', # Include the whole context field
            # 'remote_addr', # Removed as it's not a direct model field
            # 'additional_data', # Removed as it's not a model field
        )
        # Update read_only_fields if fields changed
        read_only_fields = (
            'id', 'created_at', 'user', 'organization', 'action_type',
            'action_type_display', 'content_type', 'object_id', 'object_repr',
            'changes', 'context',
            # 'additional_data', # Removed
        ) 