
# Workflow/State Machine Integration - Implementation Steps

## 1. Overview

**Feature Name:**
Workflow / State Machine Integration

**Corresponding PRD:**
`workflow_prd.md` (Simplified - Integration focus using `django-fsm`)

**Depends On:**
`Status` model (for state definitions), `AuditLogging` system (for logging transitions), `RBAC` system (for transition permissions), Celery (optional, for async side-effects), Target Models (e.g., `Product`, `Invoice`) that will have workflows applied.

**Key Features:**
Integrates `django-fsm` to add state machine capabilities to existing Django models. Defines transitions, conditions, and permissions in model methods. Triggers transitions via API actions. Logs transitions.

**Primary Location(s):**
*   Library installation: `requirements/*.txt`, `settings.py` (`INSTALLED_APPS` if needed by library features like admin integration).
*   State field (`status`): Added to target models (e.g., `api/v1/.../models.py`).
*   Transition methods (`@fsm.transition`): Added to target models.
*   Condition/Permission functions: Defined in target model's file or shared utils.
*   API Actions (`@action`): Added to target model's ViewSet (`api/v1/.../views.py`).
*   Signal receiver for Audit Log: `audit/signals.py` (or similar).

## 2. Prerequisites

[ ] Verify `Status` model is implemented and populated with necessary status slugs.
[ ] Verify `AuditLogging` system is implemented (specifically the `log_audit_event` helper or similar).
[ ] Verify `RBAC` system is implemented (specifically the ability to check permissions like `user.has_perm`).
[ ] Install required library: `pip install django-fsm`.
[ ] Add `'django_fsm'` to `INSTALLED_APPS` in `config/settings/base.py` (needed for template tags, admin integration if used).
[ ] Ensure Celery is set up if any transition side-effects need to run asynchronously.

## 3. Implementation Steps (Applied Per Target Model)

  *(These steps are performed for *each* model that requires a workflow, e.g., Product, Invoice)*

  ### 3.1 Add State Field to Target Model (`models.py`)

  [ ] **(Refactor Model)** Modify the target model (e.g., `Product` in `api/v1/features/products/models.py`).
  [ ] Ensure it has a `status` field suitable for `django-fsm`. A `CharField` referencing `Status.slug` values is common.
      ```python
      # Example modification for Product model
      from django_fsm import FSMField # Import FSMField
      # ... other imports ...
      from api.v1.base_models.common.models import Status # Import Status for reference/initial value

      class Product(Timestamped, Auditable, OrganizationScoped):
          # ... other fields ...
          status = FSMField( # Use FSMField instead of CharField
              _("Status"),
              max_length=50,
              default=Status.objects.get(slug='draft').slug, # Or use choices default 'draft'
              # choices=ProductStatus.CHOICES, # Keep choices for admin/validation if desired
              db_index=True,
              protected=True, # Prevents direct modification; changes must go through transitions
          )
          # ... rest of model ...
      ```
      *(Note: Using `FSMField` with `protected=True` is best practice)*.
  [ ] Run `makemigrations` and `migrate` for the app containing the modified model.

  ### 3.2 Define Transition Methods (`models.py`)

  [ ] **(Test First - Transitions)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` for the target model) verifying:
      *   Transitions between valid states succeed (e.g., `product.activate()` changes status from 'draft' to 'active').
      *   Attempting invalid transitions raises `django_fsm.TransitionNotAllowed`.
      *   Transitions check conditions correctly (mock condition functions).
      *   Transitions check permissions correctly (mock `user.has_perm` or the permission check function used).
      Run; expect failure (methods don't exist).
  [ ] Define methods on the target model, decorated with `@transition`.
      ```python
      # Example transitions on Product model
      from django.utils.translation import gettext_lazy as _
      from django_fsm import transition, TransitionNotAllowed
      # Assuming Status slugs 'draft', 'active', 'discontinued' exist

      # Example condition function (can be method or standalone)
      def can_activate_product(instance):
          # Example: Check if required fields are filled
          return bool(instance.description and instance.category)

      class Product(Timestamped, Auditable, OrganizationScoped):
          # ... fields including status = FSMField(...) ...

          @transition(field=status, source='draft', target='active',
                      conditions=[can_activate_product],
                      permission='products.can_activate_product') # Example permission codename
          def activate(self, user=None, reason=""): # Pass user for permission checks
              """Activates the product if conditions and permissions met."""
              # Actions DURING transition (before status changes) can go here
              print(f"Product {self.sku} being activated by {user}.")
              # Don't call self.save() here - FSMField handles it

          @transition(field=status, source='active', target='discontinued')
          def discontinue(self, reason=""):
              """Discontinues an active product."""
              # Actions DURING transition
              print(f"Product {self.sku} discontinued. Reason: {reason}")

          @transition(field=status, source='*', target='draft') # Allow moving back to draft?
          def reset_to_draft(self):
              """Resets product back to draft state."""
              print(f"Product {self.sku} reset to draft.")

          # ... rest of model ...
      ```
      *(Note: Define custom model permissions like `can_activate_product` in the model's `Meta.permissions` if using string-based permissions)*.
  [ ] Run transition tests; expect pass. Refactor.

  ### 3.3 Implement Side Effects (Signals/Hooks)

  [ ] **(Test First)** Write **Integration Test(s)** (`tests/integration/test_workflows.py` or similar) verifying side effects:
      *   Trigger a successful transition (e.g., `product.activate()`).
      *   Assert that expected side effects occurred (e.g., a notification task was queued, an AuditLog entry was created). Mock external calls (like notification service).
      Run; expect failure (side effects not implemented).
  [ ] Implement side effect logic. **Recommended: Use `django-fsm` signals.**
      ```python
      # audit/signals.py (Example connecting to FSM signal)
      from django_fsm.signals import post_transition
      from django.dispatch import receiver
      from crum import get_current_user
      from .models import AuditLog, AuditActionType
      from .utils import log_audit_event
      # Import models involved in workflows
      from api.v1.features.products.models import Product # Example

      @receiver(post_transition)
      def audit_state_transition(sender, instance, name, source, target, **kwargs):
          """Log any successful state transition managed by django-fsm."""
          # Filter specific models if needed, e.g. if not issubclass(sender, Auditable): return
          user = get_current_user()
          organization = getattr(instance, 'organization', None) # If instance is OrgScoped

          # Create context for the log
          context = {
              'transition_name': name, # Name of the transition method called
              'source_state': source,
              'target_state': target,
          }
          # Optionally add transition kwargs if passed and relevant

          log_audit_event(
              user=user,
              organization=organization,
              action_type='STATUS_CHANGE', # Or more specific like 'PRODUCT_ACTIVATED'
              content_object=instance,
              context=context
          )

          # --- Trigger other side effects (e.g., notifications) ---
          # if isinstance(instance, Product) and target == ProductStatus.ACTIVE:
          #    from services.notifications import send_product_active_notification # Example
          #    send_product_active_notification.delay(instance.pk) # Use Celery task

      ```
  [ ] Ensure this signal receiver is connected (e.g., in `audit/apps.py`).
  [ ] Run side effect tests; expect pass. Refactor.

  ### 3.4 API Integration (Views & URLs)

  [ ] **(Test First)** Write **API Test(s)** (`tests/api/test_endpoints.py` for the target model) for the transition actions:
      *   Test `POST /api/v1/products/{id}/activate/` with an authenticated user who *has* permission -> Assert 200 OK, check response status is 'active', verify AuditLog created.
      *   Test `POST /api/v1/products/{id}/activate/` when product is not in 'draft' state -> Assert 400/409 Bad Request (TransitionNotAllowed).
      *   Test `POST /api/v1/products/{id}/activate/` with user *lacking* permission -> Assert 403 Forbidden.
      *   Test transition where conditions fail -> Assert 400/409 Bad Request.
      Run; expect failure (API actions don't exist).
  [ ] Add `@action` methods to the target model's ViewSet (e.g., `ProductViewSet`).
      ```python
      # api/v1/features/products/views.py
      from rest_framework.decorators import action
      from rest_framework.response import Response
      from rest_framework import status
      from django_fsm import TransitionNotAllowed
      # ... other imports ...

      class ProductViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
          # ... queryset, serializer_class, permissions ...

          @action(detail=True, methods=['post'], url_path='activate',
                  # Add specific permission check for the action endpoint itself if needed
                  # permission_classes=[IsAuthenticated, CanActivateProductPermission]
                  )
          def activate_product(self, request, pk=None): # Use slug if lookup_field='slug'
              product = self.get_object() # Handles 404 and object permissions
              try:
                  # Pass user for permission checks within the transition decorator
                  product.activate(user=request.user)
                  # Optional: Reload instance if save didn't update the one in memory
                  # product.refresh_from_db() # If needed
                  serializer = self.get_serializer(product)
                  return Response(serializer.data)
              except TransitionNotAllowed as e:
                  return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

          @action(detail=True, methods=['post'], url_path='discontinue')
          def discontinue_product(self, request, pk=None):
              product = self.get_object()
              reason = request.data.get('reason', '') # Optional reason from payload
              try:
                  product.discontinue(user=request.user, reason=reason)
                  serializer = self.get_serializer(product)
                  return Response(serializer.data)
              except TransitionNotAllowed as e:
                  return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

          # Optional: Get available transitions
          @action(detail=True, methods=['get'], url_path='available-transitions')
          def available_transitions(self, request, pk=None):
              product = self.get_object()
              # Use django-fsm helper to get transitions allowed for the current user
              transitions = [
                  t.name for t in product.get_available_user_transitions(request.user)
              ]
              return Response({'available_transitions': transitions})

      ```
  [ ] Update URL routing (`urls.py`) in the target model's app to include the new actions if using standard DRF router (it usually handles `@action` automatically).
  [ ] Run API action tests; expect pass. Refactor.

  ### 3.5 Admin Integration (Optional)

  [ ] Install `django-fsm-admin` (`pip install django-fsm-admin`).
  [ ] Add `'fsm_admin'` to `INSTALLED_APPS`.
  [ ] Inherit from `FSMAdminMixin` in the target model's Admin class (e.g., `ProductAdmin`).
      ```python
      # api/v1/features/products/admin.py
      from fsm_admin.mixins import FSMAdminMixin
      # ... other imports ...

      @admin.register(Product)
      class ProductAdmin(FSMAdminMixin, admin.ModelAdmin): # Add FSMAdminMixin
          # ... existing admin config ...
          # Specify the state field for the admin buttons
          fsm_field = ['status',]
      ```
  [ ] **(Manual Test):** Verify transition buttons appear in the Django Admin detail view for the model and that they work correctly (respecting permissions/conditions if the admin user isn't superuser).

  ### 3.6 Repeat for Other Models

  [ ] Repeat steps 3.1 - 3.5 (and potentially 3.6 if needed) for other models requiring workflows (e.g., `Invoice`, `PurchaseOrder`).

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`). Verify workflow tests and audit log tests pass for transitions.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov`). Ensure transition methods, conditions, permissions, and signal handlers are covered.
[ ] Manually test key workflow transitions via API client and/or Admin UI. Check Audit Log entries.
[ ] Review API documentation draft for transition actions.

## 5. Follow-up Actions

[ ] Address TODOs (e.g., implement missing permission checks, condition logic, side effects).
[ ] Create Pull Request(s).
[ ] Update API documentation with details on transition endpoints and permissions.
[ ] Configure Celery workers if async side effects were implemented.

--- END OF FILE workflow_integration_steps.md ---