import pytest
from api.v1.base_models.organization.tests.factories import OrganizationTypeFactory
from api.v1.base_models.organization.serializers import OrganizationTypeSerializer

@pytest.mark.django_db
class TestOrganizationTypeSerializer:
    @pytest.fixture
    def org_type(self):
        return OrganizationTypeFactory()

    def test_serializer_output_format(self, org_type):
        """Test that the serializer produces the expected output format"""
        serializer = OrganizationTypeSerializer(org_type)
        data = serializer.data

        # Verify all expected fields are present
        assert 'name' in data
        assert 'description' in data

        # Verify field values match the model
        assert data['name'] == org_type.name
        assert data['description'] == org_type.description

    def test_serializer_read_only_fields(self, org_type):
        """Test that the serializer fields are read-only"""
        serializer = OrganizationTypeSerializer(org_type)
        assert serializer.fields['name'].read_only
        assert serializer.fields['description'].read_only 