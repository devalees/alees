
**Overall Goal:** Implement the `OrganizationScoped` abstract model and the `OrganizationScopedViewSetMixin` to enforce multi-tenancy.

---


### Task Block 3: Implement and Test ViewSet Mixin - Creation Logic (`perform_create`) with Mocked RBAC

**Goal:** Verify the mixin's creation logic correctly determines the target organization, calls the (mocked) permission check, and saves/denies accordingly.

**Steps:**

1.  **(Test First) Write `perform_create` Tests:** Add tests to `TestOrganizationScopedViewSetGetQueryset` (rename the class appropriately, e.g., `TestOrganizationScopedViewSetMixin`) to cover `perform_create` scenarios. Use `pytest-mock` (`mocker` fixture).
    ```python
    # core/tests/integration/test_orgscoped_views.py (continued)
    from unittest.mock import patch # Or use mocker fixture from pytest-mock
    from rest_framework.exceptions import PermissionDenied, ValidationError
    from rest_framework.mixins import CreateModelMixin
    from rest_framework import serializers # For a minimal serializer

    # --- Minimal Serializer for Testing Create ---
    class ConcreteScopedSerializer(serializers.ModelSerializer):
        # Explicitly require organization ID for writing in this test setup
        organization = serializers.PrimaryKeyRelatedField(
            queryset=Organization.objects.all(), write_only=True
        )
        class Meta: model = ConcreteScopedModel; fields = ['id', 'name', 'organization']
    # --- End Test Serializer ---

    # --- Update Test ViewSet to include Create ---
    class ConcreteScopedViewSet(OrganizationScopedViewSetMixin, CreateModelMixin, ReadOnlyModelViewSet): # Add CreateModelMixin
        queryset = ConcreteScopedModel.objects.all()
        serializer_class = ConcreteScopedSerializer # Use the test serializer
    # --- End Test ViewSet Update ---

    class TestOrganizationScopedViewSetMixin: # Renamed test class
        # ... existing fixtures and get_queryset tests ...

        def test_perform_create_success_with_permission(self, factory, mocker, user_a, org_a):
            """Verify successful creation when permission check passes."""
            view = ConcreteScopedViewSet(action='create') # Simulate action
            # Mock the RBAC check function used within perform_create
            mocked_perm_check = mocker.patch('core.views.has_perm_in_org') # Adjust path
            mocked_perm_check.return_value = True

            serializer = view.get_serializer(data={'name': 'New Item A', 'organization': org_a.pk})
            serializer.is_valid(raise_exception=True)

            request = factory.post('/fake-create/', data=serializer.validated_data)
            force_authenticate(request, user=user_a)
            view.request = request # Set request on view instance for perform_create

            view.perform_create(serializer) # Call the method directly

            # Assertions
            assert ConcreteScopedModel.objects.count() == 1
            new_item = ConcreteScopedModel.objects.first()
            assert new_item.name == 'New Item A'
            assert new_item.organization == org_a
            # Verify the permission check was called correctly
            mocked_perm_check.assert_called_once_with(
                user_a, f'{ConcreteScopedModel._meta.app_label}.add_{ConcreteScopedModel._meta.model_name}', org_a
            )

        def test_perform_create_fail_without_permission(self, factory, mocker, user_a, org_b):
            """Verify creation fails if permission check returns False."""
            view = ConcreteScopedViewSet(action='create')
            mocked_perm_check = mocker.patch('core.views.has_perm_in_org')
            mocked_perm_check.return_value = False # Simulate permission denied

            serializer = view.get_serializer(data={'name': 'New Item B', 'organization': org_b.pk})
            serializer.is_valid(raise_exception=True)

            request = factory.post('/fake-create/', data=serializer.validated_data)
            force_authenticate(request, user=user_a)
            view.request = request

            with pytest.raises(PermissionDenied):
                view.perform_create(serializer)

            assert ConcreteScopedModel.objects.count() == 0
            mocked_perm_check.assert_called_once_with(
                user_a, f'{ConcreteScopedModel._meta.app_label}.add_{ConcreteScopedModel._meta.model_name}', org_b
            )

        def test_perform_create_fail_missing_organization(self, factory, user_a):
            """Verify validation error if organization is missing."""
            view = ConcreteScopedViewSet(action='create')
            serializer = view.get_serializer(data={'name': 'New Item Missing Org'}) # Missing org
            # Validation should ideally happen in serializer or perform_create check

            request = factory.post('/fake-create/', data={'name': 'New Item Missing Org'})
            force_authenticate(request, user=user_a)
            view.request = request

            # Expect perform_create itself to raise the error
            with pytest.raises(ValidationError) as excinfo:
                 # Need a way to call perform_create with invalid serializer if validation is there
                 # If validation is in the serializer triggered by is_valid:
                 # assert not serializer.is_valid()
                 # assert 'organization' in serializer.errors
                 # If validation is in perform_create:
                 serializer_mock_valid = view.get_serializer(data={'name': 'New Item Missing Org'}) # Assume it could be valid initially
                 serializer_mock_valid.is_valid() # Simulate passing basic validation
                 view.perform_create(serializer_mock_valid)

            assert 'organization' in str(excinfo.value) # Check error message relates to org
            assert ConcreteScopedModel.objects.count() == 0

        # Add test case for non-existent organization PK if desired
    ```
    *   **Run:** `pytest core/tests/integration/test_orgscoped_views.py`. Expect failures related to `perform_create` or the mocked permission check. **(Red)**

2.  **(Implement) Define `perform_create` in Mixin:**
    *   Add the `perform_create` method to `OrganizationScopedViewSetMixin` in `core/views.py` (as shown in the previous example). Ensure it imports and calls the (currently placeholder/mock target) `has_perm_in_org` function.
    *   Handle the case where `organization` isn't provided (raise `ValidationError`).
    *   Call `serializer.save(organization=target_organization)`.

3.  **(Test & Refactor)**
    *   Run `perform_create` tests again: `pytest core/tests/integration/test_orgscoped_views.py`. They should now pass (with the RBAC check mocked). **(Green)**
    *   Refactor `perform_create` or test setup if needed.

**Outcome of Task Block 3:** The `perform_create` logic is implemented and verified structurally using mocked permissions.

---
