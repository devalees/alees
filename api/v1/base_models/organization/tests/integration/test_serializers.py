import pytest
from api.v1.base_models.organization.tests.factories import OrganizationTypeFactory
from api.v1.base_models.organization.serializers import OrganizationTypeSerializer

@pytest.mark.django_db
class TestOrganizationTypeSerializer:
    @pytest.fixture
    def org_type(self):
        return OrganizationTypeFactory()

    @pytest.fixture
    def serializer(self, org_type):
        return OrganizationTypeSerializer(instance=org_type)

    def test_serializer_output_format(self, serializer, org_type):
        """Test that serializer output matches expected format"""
        data = serializer.data
        assert 'name' in data
        assert 'description' in data
        assert data['name'] == org_type.name
        assert data['description'] == org_type.description

    def test_serializer_read_only_fields(self, serializer):
        """Test that read-only fields are properly handled"""
        data = serializer.data
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'created_by' in data
        assert 'updated_by' in data 