import pytest
# from django.db import models # No longer needed here
from django.db import IntegrityError
from django.core.exceptions import FieldError
# from core.models import OrganizationScoped # No longer needed directly
from core.tests_app.models import ConcreteScopedModel # Import from new location
from django.apps import apps
from api.v1.base_models.organization.tests.factories import OrganizationFactory

# --- Concrete model JUST for testing the abstract one ---
# class ConcreteScopedModel(OrganizationScoped):
#     name = models.CharField(max_length=100)
#     # Important: Define app_label so Django treats it as part of an app for testing migrations/DB table creation
#     class Meta:
#         app_label = 'core'
# --- End Test Model ---

@pytest.mark.django_db
class TestOrganizationScopedModelStructure:
    def test_organization_field_exists(self):
        """Verify the 'organization' field is added by the mixin."""
        try:
            field = ConcreteScopedModel._meta.get_field('organization')
            Organization = apps.get_model('api_v1_organization', 'Organization')
            assert field is not None
            assert field.remote_field.model == Organization
            assert not field.null  # Should be required
            assert field.remote_field.on_delete.__name__ == 'PROTECT'  # Check on_delete
            assert field.db_index  # Check index
        except FieldError:
            pytest.fail("'organization' field not found on ConcreteScopedModel")

    def test_cannot_create_without_organization(self):
        """Verify IntegrityError if organization is not provided."""
        with pytest.raises(IntegrityError):
            # Direct creation without org should fail DB constraint
            ConcreteScopedModel.objects.create(name="Test Name No Org")  # Missing organization

    def test_can_create_with_organization(self):
        """Verify creation succeeds when organization is provided."""
        org = OrganizationFactory()
        instance = ConcreteScopedModel.objects.create(name="Test Name With Org", organization=org)
        assert instance.pk is not None
        assert instance.organization == org
        assert ConcreteScopedModel.objects.count() == 1 