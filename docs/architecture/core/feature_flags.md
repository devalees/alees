# Feature Flags Management

## Overview

This document outlines the feature flags management strategy for the Alees ERP system, using `django-flags` as the primary feature flag management solution.

## Feature Flags Configuration

### Storage Options

1. **Redis Storage** (Recommended for Production)
   - Configure in settings:
     ```python
     FEATURE_FLAGS_STORAGE = 'redis'
     FEATURE_FLAGS_REDIS_URL = 'redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/4'  # Using DB 4
     ```

2. **Database Storage** (Default)
   - Configure in settings:
     ```python
     FEATURE_FLAGS_STORAGE = 'database'
     ```

3. **Cache Storage**
   - Configure in settings:
     ```python
     FEATURE_FLAGS_STORAGE = 'cache'
     ```

### Flag Naming Convention

- Format: `{module}.{feature}.{action}`
- Examples:
  - `auth.two_factor.enabled`
  - `billing.invoice_auto_generate`
  - `project.task_assignments`

## Feature Flag Types

1. **Boolean Flags**
   - Simple on/off switches
   - Example: `auth.two_factor.enabled`

2. **User-Based Flags**
   - Enabled for specific users or groups
   - Example: `project.beta_features`

3. **Percentage-Based Flags**
   - Enabled for a percentage of users
   - Example: `ui.new_dashboard`

4. **Time-Based Flags**
   - Enabled during specific time periods
   - Example: `marketing.promotion_active`

## Feature Rollout Process

### 1. Development Phase

1. **Create Feature Flag**
   ```python
   from core.flags import FeatureFlagsManager
   
   flags_manager = FeatureFlagsManager()
   flags_manager.create_flag(
       name='project.new_feature',
       description='New project management feature',
       default=False
   )
   ```

2. **Implement Feature with Flag Check**
   ```python
   from core.flags import FeatureFlagsManager
   
   flags_manager = FeatureFlagsManager()
   
   def new_feature_view(request):
       if flags_manager.is_enabled('project.new_feature', request):
           # New feature implementation
           pass
       else:
           # Old feature implementation
           pass
   ```

### 2. Testing Phase

1. **Enable for Test Environment**
   ```python
   # config/settings/test.py
   FLAGS = {
       'project.new_feature': [{'condition': 'boolean', 'value': True}]
   }
   ```

2. **Write Tests**
   ```python
   from django.test import TestCase
   from core.flags import FeatureFlagsManager
   
   class NewFeatureTests(TestCase):
       def setUp(self):
           self.flags_manager = FeatureFlagsManager()
           self.flags_manager.create_flag(
               name='project.new_feature',
               description='Test flag',
               default=True
           )
   
       def test_new_feature_enabled(self):
           self.assertTrue(self.flags_manager.is_enabled('project.new_feature'))
   ```

### 3. Staging Phase

1. **Enable for Beta Users**
   ```python
   # Enable for specific users
   FLAGS = {
       'project.new_feature': [
           {'condition': 'user', 'value': 'beta_user@example.com'}
       ]
   }
   ```

2. **Monitor Performance**
   - Track feature usage
   - Monitor error rates
   - Collect user feedback

### 4. Production Rollout

1. **Percentage-Based Rollout**
   ```python
   # Enable for 10% of users
   FLAGS = {
       'project.new_feature': [
           {'condition': 'percent', 'value': 10}
       ]
   }
   ```

2. **Gradual Increase**
   - Increase percentage weekly
   - Monitor metrics
   - Address issues

3. **Full Rollout**
   ```python
   # Enable for all users
   FLAGS = {
       'project.new_feature': [
           {'condition': 'boolean', 'value': True}
       ]
   }
   ```

## Implementation Examples

### 1. View-Level Feature Flag

```python
from django.views.generic import View
from core.flags import FeatureFlagsManager

class ProjectView(View):
    def get(self, request):
        flags_manager = FeatureFlagsManager()
        if flags_manager.is_enabled('project.new_dashboard', request):
            return self.new_dashboard(request)
        return self.old_dashboard(request)
```

### 2. Template-Level Feature Flag

```html
{% load feature_flags %}
{% flag_enabled 'ui.new_navigation' as new_nav %}
{% if new_nav %}
    {% include "new_navigation.html" %}
{% else %}
    {% include "old_navigation.html" %}
{% endif %}
```

### 3. API-Level Feature Flag

```python
from rest_framework.views import APIView
from core.flags import FeatureFlagsManager

class ProjectAPIView(APIView):
    def get_serializer_class(self):
        flags_manager = FeatureFlagsManager()
        if flags_manager.is_enabled('api.v2.serializers', self.request):
            return ProjectV2Serializer
        return ProjectV1Serializer
```

## Monitoring and Management

### 1. Flag Status Dashboard

```python
from django.contrib.admin import AdminSite
from flags.admin import FlagAdmin
from flags.models import Flag

class FeatureFlagsAdminSite(AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        app_list.append({
            'name': 'Feature Flags',
            'app_label': 'flags',
            'models': [
                {
                    'name': 'Flags',
                    'object_name': 'Flag',
                    'admin_url': '/admin/flags/flag/',
                    'view_only': False,
                }
            ]
        })
        return app_list
```

### 2. Usage Tracking

```python
from django.db import models
from django.utils import timezone

class FeatureFlagUsage(models.Model):
    flag_name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    enabled = models.BooleanField()
    timestamp = models.DateTimeField(default=timezone.now)
```

## Best Practices

1. **Naming**
   - Use consistent naming conventions
   - Make names descriptive
   - Include module/feature context

2. **Documentation**
   - Document all feature flags
   - Include purpose and rollout plan
   - Update documentation with changes

3. **Cleanup**
   - Remove unused flags
   - Archive old flags
   - Update documentation

4. **Testing**
   - Test both enabled and disabled states
   - Include flag tests in CI/CD
   - Test flag combinations

5. **Monitoring**
   - Track flag usage
   - Monitor performance impact
   - Alert on issues 