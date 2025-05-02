import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from rest_framework import serializers

# Assuming models and serializers are in the same app structure
from api.v1.base_models.organization.models import (
    Organization, OrganizationType, OrganizationMembership
)
from api.v1.base_models.organization.serializers import (
    OrganizationSerializer, OrganizationTypeSerializer, OrganizationMembershipSerializer
)
# Assuming factories are available for related models
from api.v1.base_models.organization.tests.factories import (
    OrganizationTypeFactory,
    OrganizationFactory,
    OrganizationMembershipFactory
)
from api.v1.base_models.user.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

# --- Test OrganizationTypeSerializer ---

# ... rest of the file ...