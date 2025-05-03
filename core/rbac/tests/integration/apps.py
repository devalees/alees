from django.apps import AppConfig

APP_LABEL = 'rbac_integration_test_app'

class RBACIntegrationTestAppConfig(AppConfig):
    # Point to the integration test module/package itself
    name = 'core.rbac.tests.integration' 
    label = APP_LABEL
    verbose_name = "RBAC Integration Test App" 