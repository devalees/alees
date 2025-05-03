from rest_framework import serializers
from .models import ConcreteScopedModel
from api.v1.base_models.organization.models import Organization # Import Organization

class ConcreteScopedModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConcreteScopedModel
        fields = ['id', 'name', 'organization'] # Include fields needed for test assertions
        read_only_fields = ['organization'] # Make organization read-only by default

# --- Minimal Serializer for Testing Create --- (As per impl_tasks.md)
class ConcreteCreateScopedSerializer(serializers.ModelSerializer):
    # Explicitly require organization ID for writing in this test setup
    # And make it available in validated_data
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), 
        # write_only=True, # REMOVE THIS
        required=True 
    )
    class Meta:
        model = ConcreteScopedModel
        fields = ['id', 'name', 'organization']
        # You might want read_only_fields = ['id'] if you don't want ID writeable
# --- End Test Serializer --- 