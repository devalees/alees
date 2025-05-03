import pytest
from pytest_factoryboy import register

# Adjust import paths based on actual factory locations
try:
    from api.v1.base_models.user.tests.factories import UserFactory
    register(UserFactory)
except ImportError:
    print("Warning: Could not import or register UserFactory. Tests depending on it may fail.")

try:
    from api.v1.base_models.organization.tests.factories import OrganizationFactory
    register(OrganizationFactory)
except ImportError:
    print("Warning: Could not import or register OrganizationFactory. Tests depending on it may fail.")

# If other factories are needed by audit tests later, register them here too
