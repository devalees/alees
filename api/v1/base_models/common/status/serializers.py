from rest_framework import serializers
from .models import Status

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = [
            'slug',
            'name',
            'description',
            'category',
            'color',
            'custom_fields',
            # Include Timestamped/Auditable fields if needed by API consumers
            # 'created_at',
            # 'updated_at',
            # 'created_by',
            # 'updated_by',
        ]
        # Generally read-only from an API perspective
        read_only_fields = fields 