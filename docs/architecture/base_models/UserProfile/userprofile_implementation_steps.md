Okay, let's generate the implementation steps for the `UserProfile` model, which extends the built-in Django `User` model. This follows the `UserProfile.md` PRD and our standard implementation steps template, incorporating TDD.

**Important Decision:** The PRD Section 3.2 mentions choosing a pattern for **Organizational Relationships** (Direct FK/M2M on Profile OR Dedicated Membership Model). This decision impacts the `UserProfile` model fields and related logic. For these steps, I will assume the **Simpler Pattern A initially: Direct FK on Profile** (e.g., `primary_organization`), acknowledging that a `Membership` model might be added later if more complex role/org relationships are needed. Please adjust if the `Membership` model is preferred from the start.

--- START OF FILE userprofile_implementation_steps.md ---

# UserProfile - Implementation Steps

## 1. Overview

**Model Name:**
`UserProfile`

**Corresponding PRD:**
`UserProfile.md` (Refined version with Username Login + Custom Fields)

**Depends On:**
Django `User` model (`settings.AUTH_USER_MODEL`), `Timestamped`, `Auditable`, `Organization` (for FK), `FileStorage` (for profile picture FK - *Implement FileStorage first if strict FK needed, otherwise use nullable initially or defer picture field*).

**Key Features:**
Extends Django User with ERP-specific fields (job title, phone, manager), preferences (language, timezone), organizational links, custom fields, and signals for auto-creation.

**Primary Location(s):**
`api/v1/base_models/user/` (Following chosen project structure)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `Organization`) are implemented and migrated.
[ ] Verify Django `auth` app is configured and `AUTH_USER_MODEL` is correctly set (likely default `auth.User`).
[ ] Ensure the `user` app structure exists (`api/v1/base_models/user/`).
[ ] Ensure `factory-boy` is set up. Create `UserFactory` if not already done.
[ ] Ensure `FileStorage` model exists if implementing `profile_picture` with a strict ForeignKey immediately. *(If FileStorage is later, define `profile_picture` field initially as nullable/blank or omit)*.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First - Basic)**
      Write **Unit Test(s)** (`tests/unit/test_models.py`) verifying:
      *   A `UserProfile` instance can be created and linked to a `User` instance (created via `UserFactory`).
      *   The `__str__` method returns the associated `user.username`.
      *   Inherited `created_at`, `updated_at`, `created_by`, `updated_by` fields exist (assuming base model tests cover population).
      Run; expect failure (`UserProfile` doesn't exist).
  [ ] Define the `UserProfile` class in `api/v1/base_models/user/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`.
  [ ] Define the core `OneToOneField` link to `User`:
      ```python
      from django.conf import settings
      from django.db import models
      from core.models import Timestamped, Auditable # Assuming core app location
      # Import Organization, FileStorage based on final location
      from api.v1.base_models.organization.models import Organization
      # from api.v1.base_models.common.models import FileStorage # Example

      class UserProfile(Timestamped, Auditable):
          user = models.OneToOneField(
              settings.AUTH_USER_MODEL,
              on_delete=models.CASCADE, # Delete profile if user is deleted
              related_name='profile',
              primary_key=True, # Often makes sense for OneToOne profile
          )
          # ... rest of fields ...

          def __str__(self):
              return str(self.user.username)

          class Meta:
              verbose_name = "User Profile"
              verbose_name_plural = "User Profiles"
      ```
  [ ] Define basic attribute fields from PRD Section 3.2 (Examples):
      ```python
      job_title = models.CharField(max_length=100, blank=True, null=True)
      employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True) # Unique must allow null
      phone_number = models.CharField(max_length=30, blank=True, null=True) # Consider django-phonenumber-field later
      # profile_picture = models.ForeignKey(FileStorage, on_delete=models.SET_NULL, null=True, blank=True) # If FileStorage exists
      manager = models.ForeignKey(
          settings.AUTH_USER_MODEL,
          on_delete=models.SET_NULL,
          related_name='direct_reports',
          null=True,
          blank=True
      )
      date_of_birth = models.DateField(null=True, blank=True)
      # ... other employment fields ...
      employment_type = models.CharField(max_length=50, blank=True, null=True) # Add choices later
      ```
  [ ] Define Preferences Fields (PRD 3.4):
      ```python
      language = models.CharField(max_length=10, default=settings.LANGUAGE_CODE)
      timezone = models.CharField(max_length=60, default=settings.TIME_ZONE)
      notification_preferences = models.JSONField(default=dict, blank=True)
      ```
  [ ] Define Organizational Relationships (Assuming **Option A: Direct FK** initially):
      ```python
      # Example: User belongs to one primary org, potentially many others via roles/teams later
      primary_organization = models.ForeignKey(
          Organization,
          on_delete=models.PROTECT, # Don't delete Org if users assigned
          related_name='primary_members', # Or similar
          null=True, # Allow users without a primary org? Decide based on reqs.
          blank=True
      )
      # Add Department/Team FKs/M2Ms here if using this pattern
      ```
  [ ] Define Custom Fields:
      ```python
      custom_fields = models.JSONField(default=dict, blank=True)
      ```
  [ ] Implement the `__str__` method (already done above).
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `UserProfileFactory` in `api/v1/base_models/user/tests/factories.py`:
      ```python
      # Need UserFactory first
      from django.contrib.auth import get_user_model
      import factory
      from factory.django import DjangoModelFactory
      from ..models import UserProfile
      # Import other factories if needed (Org, FileStorage)
      from api.v1.base_models.organization.tests.factories import OrganizationFactory

      User = get_user_model()

      class UserFactory(DjangoModelFactory):
          class Meta:
              model = User
              django_get_or_create = ('username',)

          username = factory.Sequence(lambda n: f'user{n}')
          email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
          first_name = factory.Faker('first_name')
          last_name = factory.Faker('last_name')
          is_active = True

          # Ensure profile is created if needed by other factories/tests
          # profile = factory.RelatedFactory('api.v1.base_models.user.tests.factories.UserProfileFactory', factory_related_name='user')

      class UserProfileFactory(DjangoModelFactory):
          class Meta:
              model = UserProfile

          user = factory.SubFactory(UserFactory, profile=None) # Avoid recursion if UserFactory defines profile
          job_title = factory.Faker('job')
          phone_number = factory.Faker('phone_number')
          language = 'en'
          timezone = 'UTC'
          primary_organization = factory.SubFactory(OrganizationFactory)
          custom_fields = {}
          # Add other fields
      ```
  [ ] **(Test)** Write a simple test ensuring `UserProfileFactory` creates valid `UserProfile` and linked `User` instances.

  ### 3.3 Signal for Auto-Creation (`signals.py` or `models.py`)

  [ ] **(Test First)**
      Write **Integration Test(s)** (`tests/integration/test_signals.py`) using `@pytest.mark.django_db`.
      *   Test that creating a *new* `User` instance automatically creates a linked `UserProfile`.
      *   Test that saving an *existing* `User` does *not* create a new `UserProfile` or error out.
      Run; expect failure.
  [ ] Create `api/v1/base_models/user/signals.py`. Define a `post_save` receiver for the `User` model:
      ```python
      # api/v1/base_models/user/signals.py
      from django.conf import settings
      from django.db.models.signals import post_save
      from django.dispatch import receiver
      from .models import UserProfile

      User = settings.AUTH_USER_MODEL

      @receiver(post_save, sender=User)
      def create_or_update_user_profile(sender, instance, created, **kwargs):
          """
          Create or update the user profile when a user is saved.
          """
          if created:
              UserProfile.objects.create(user=instance)
          # Optionally update profile fields based on user fields if needed:
          # instance.profile.save() # Example if profile has fields derived from User
  ```
  [ ] Import and connect the signal receiver in `api/v1/base_models/user/apps.py`:
      ```python
      # api/v1/base_models/user/apps.py
      from django.apps import AppConfig

      class UserAppConfig(AppConfig):
          default_auto_field = 'django.db.models.BigAutoField'
          name = 'api.v1.base_models.user' # Adjust to your actual app path

          def ready(self):
              try:
                  import api.v1.base_models.user.signals # Adjust import path
              except ImportError:
                  pass
      ```
  [ ] Ensure this AppConfig is registered correctly (likely via the `base_models/apps.py` if using that structure).
  [ ] Run signal tests; expect pass. Refactor.

  ### 3.4 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/user/admin.py`.
  [ ] Define `UserProfileInline(admin.StackedInline)`:
      ```python
      from django.contrib import admin
      from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
      from django.contrib.auth.models import User # Or settings.AUTH_USER_MODEL
      from .models import UserProfile

      class UserProfileInline(admin.StackedInline):
          model = UserProfile
          can_delete = False
          verbose_name_plural = 'Profile'
          fk_name = 'user'
          # Define fields to display/edit in the inline
          fields = ('job_title', 'employee_id', 'phone_number', 'manager', 'primary_organization', 'language', 'timezone', 'custom_fields') # Add others
          # Consider readonly fields if applicable
      ```
  [ ] Define a new `UserAdmin` inheriting from Django's `BaseUserAdmin` and including the inline:
      ```python
      class CustomUserAdmin(BaseUserAdmin):
          inlines = (UserProfileInline,)
          list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_organization') # Example
          list_select_related = ('profile', 'profile__primary_organization') # Optimize list view

          def get_inline_instances(self, request, obj=None):
              if not obj:
                  return list()
              return super().get_inline_instances(request, obj)

          @admin.display(description='Organization') # Example display field
          def get_organization(self, instance):
              if hasattr(instance, 'profile'):
                  return instance.profile.primary_organization
              return None
      ```
  [ ] Unregister the default `UserAdmin` and register the custom one:
      ```python
      admin.site.unregister(User) # Or settings.AUTH_USER_MODEL
      admin.site.register(User, CustomUserAdmin) # Or settings.AUTH_USER_MODEL
      ```
  [ ] **(Manual Test):** Verify profile fields appear inline when creating/editing Users in Django Admin. Verify profile created automatically for new users.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.user`.
  [ ] **Review generated migration file carefully** (creating UserProfile table, OneToOneField, other fields, FKs).
  [ ] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  *(Focus on UserProfile serializer first. A User serializer might also be needed)*
  [ ] **(Test First - Validation)** Write Unit Tests (`tests/unit/test_serializers.py`) for `UserProfileSerializer` validation (e.g., timezone format, language code validity if using choices, custom field validation).
  [ ] Define `UserProfileSerializer` in `api/v1/base_models/user/serializers.py`:
      ```python
      from rest_framework import serializers
      from .models import UserProfile
      # Import other serializers if nesting (User, Org)

      class UserProfileSerializer(serializers.ModelSerializer):
          # Optionally include read-only user fields
          username = serializers.CharField(source='user.username', read_only=True)
          email = serializers.EmailField(source='user.email', read_only=True)
          first_name = serializers.CharField(source='user.first_name', read_only=True)
          last_name = serializers.CharField(source='user.last_name', read_only=True)
          # Add nested serializers for related fields if needed (read-only recommended)
          # primary_organization = OrganizationSummarySerializer(read_only=True)
          # manager = UserSummarySerializer(read_only=True)

          class Meta:
              model = UserProfile
              # List fields from UserProfile model + optional read-only User fields
              fields = [
                  'user', # Usually expose the ID only unless read-only nested
                  'username', 'email', 'first_name', 'last_name', # Read-only from User
                  'job_title', 'employee_id', 'phone_number', # etc
                  'language', 'timezone', 'notification_preferences',
                  'primary_organization', # Expose Org ID for writing, or nested for reading
                  'manager', # Expose User ID for writing, or nested for reading
                  'custom_fields',
                  'created_at', 'updated_at', # From Timestamped
              ]
              read_only_fields = ('user', 'created_at', 'updated_at') # User link usually set internally
      ```
  [ ] Implement `validate_custom_fields` method to validate against external schema.
  [ ] Run validation tests; expect pass. Refactor.
  [ ] **(Test First - Representation)** Write Integration Tests verifying serializer output structure.
  [ ] Customize representation if needed.
  [ ] Run representation tests; expect pass.

  ### 3.7 API ViewSet Definition (`views.py`)

  *(Focus on profile endpoints, User CRUD might be separate)*
  [ ] **(Test First)** Write basic API Tests (`tests/api/test_endpoints.py`) for expected profile endpoints (e.g., `/api/v1/profiles/me/`) checking for authentication (401/403).
  [ ] Define `UserProfileViewSet` (perhaps using `RetrieveUpdateAPIView` for `/profiles/me/` or extending `ModelViewSet` for admin management `/users/{user_id}/profile/`).
      ```python
      from rest_framework import generics, permissions, viewsets
      from .models import UserProfile
      from .serializers import UserProfileSerializer
      # Import custom permissions if needed

      # Option 1: Endpoint for user to manage their own profile
      class MyProfileView(generics.RetrieveUpdateAPIView):
          serializer_class = UserProfileSerializer
          permission_classes = [permissions.IsAuthenticated] # Must be logged in

          def get_object(self):
              # Return the profile linked to the requesting user
              return UserProfile.objects.get(user=self.request.user)

      # Option 2: Admin endpoint to manage any profile (nested under user?)
      # class UserProfileAdminViewSet(viewsets.ModelViewSet): # ReadOnly or full CRUD?
      #     queryset = UserProfile.objects.select_related('user', 'primary_organization', 'manager').all()
      #     serializer_class = UserProfileSerializer
      #     permission_classes = [permissions.IsAdminUser] # Example: Only Admins
      #     # Add filtering/lookup based on user_id from URL if nested
      ```
  [ ] Configure `queryset`, `serializer_class`, `permission_classes`, `authentication_classes`.
  [ ] Run basic permission tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [ ] Define URL patterns in `api/v1/base_models/user/urls.py` for the chosen views (e.g., `path('profiles/me/', views.MyProfileView.as_view(), name='my-profile')`).
  [ ] Include these URLs in `api/v1/base_models/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect correct status codes (200 for GET, 401/403 if not authenticated).

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - MyProfile)** Write tests for `GET` and `PUT`/`PATCH` on `/api/v1/profiles/me/` using `authenticated_client`. Test updating profile fields, preferences, custom fields. Test validation errors. Run; expect failure.
  [ ] Implement update logic in `MyProfileView` (DRF generics handle much of it). Ensure field-level permissions checked by serializer.
  [ ] Run MyProfile tests; expect pass. Refactor.
  [ ] *(If Admin endpoints implemented)* Write CRUD tests for those endpoints using `admin_client`, testing permissions and functionality.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov`).
[ ] Manually test profile viewing/editing via API client. Check Django Admin integration.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Decide on and implement final User-Organization relationship pattern if deferred.

--- END OF FILE userprofile_implementation_steps.md ---