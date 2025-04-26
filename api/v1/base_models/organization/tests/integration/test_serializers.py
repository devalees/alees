from django.test import TestCase
from rest_framework.test import APITestCase
from api.v1.base_models.organization.tests.factories import OrganizationTypeFactory
from api.v1.base_models.organization.serializers import OrganizationTypeSerializer

class OrganizationTypeSerializerTests(APITestCase):
    def setUp(self):
        self.org_type = OrganizationTypeFactory()

    def test_serializer_output_format(self):
        """Test that the serializer produces the expected output format"""
        serializer = OrganizationTypeSerializer(self.org_type)
        data = serializer.data

        # Verify all expected fields are present
        self.assertIn('name', data)
        self.assertIn('description', data)

        # Verify field values match the model
        self.assertEqual(data['name'], self.org_type.name)
        self.assertEqual(data['description'], self.org_type.description)

    def test_serializer_read_only_fields(self):
        """Test that the serializer fields are read-only"""
        serializer = OrganizationTypeSerializer(self.org_type)
        self.assertTrue(serializer.fields['name'].read_only)
        self.assertTrue(serializer.fields['description'].read_only) 