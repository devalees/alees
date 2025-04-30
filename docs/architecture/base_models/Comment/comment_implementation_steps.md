
# Comment - Implementation Steps

## 1. Overview

**Model Name:**
`Comment`

**Corresponding PRD:**
`comment_prd.md` (Simplified version)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `FileStorage`, `Organization`, `ContentType` framework, `django-taggit` (if using tags). Requires Custom Field Definition mechanism if used.

**Key Features:**
Allows users to add threaded comments (replies) with optional file attachments to various business objects using Generic Relations. Includes basic status/moderation, custom fields, and organization scoping.

**Primary Location(s):**
`api/v1/features/collaboration/` (Assuming a new `collaboration` feature app/group) or `api/v1/base_models/common/`. Let's assume **`collaboration`**.

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `FileStorage`, `Organization`, `ContentType`) are implemented and migrated.
[ ] Ensure `django-taggit` is installed/configured if using tags (though not explicitly listed in final PRD fields, `tags` might be added later).
[ ] **Create new Django app:** `python manage.py startapp collaboration`.
[ ] Add `'api.v1.features.collaboration'` (adjust path) to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization`, `FileStorage`, and representative parent objects (e.g., `Product`) exist.
[ ] Define `CommentStatus` choices (e.g., in `collaboration/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `collaboration`) verifying:
      *   `Comment` creation with required fields (`user`, `content`, `content_type`, `object_id`, `organization`).
      *   FKs (`user`, `parent`, `content_type`) work.
      *   GFK (`content_object`) resolves correctly to a parent instance.
      *   M2M (`attachments`) works.
      *   Default values (`is_edited`, `status`, `custom_fields`).
      *   `parent` link creates basic thread structure.
      *   `__str__` method works. Inheritance works.
      Run; expect failure (`Comment` doesn't exist).
  [ ] Define the `Comment` class in `api/v1/features/collaboration/models.py`.
  [ ] Add inheritance: `Timestamped`, `Auditable`, `OrganizationScoped`.
      ```python
      # api/v1/features/collaboration/models.py
      from django.conf import settings
      from django.contrib.contenttypes.fields import GenericForeignKey
      from django.contrib.contenttypes.models import ContentType
      from django.db import models
      from django.utils.translation import gettext_lazy as _

      from core.models import Timestamped, Auditable, OrganizationScoped # Adjust path
      # Adjust path based on FileStorage location
      from api.v1.base_models.common.models import FileStorage

      class CommentStatus:
          VISIBLE = 'VISIBLE'
          HIDDEN = 'HIDDEN' # e.g., deleted by user or moderator
          PENDING = 'PENDING_MODERATION'
          CHOICES = [
              (VISIBLE, _('Visible')),
              (HIDDEN, _('Hidden/Deleted')),
              (PENDING, _('Pending Moderation')),
          ]

      class Comment(Timestamped, Auditable, OrganizationScoped):
          # user field from Auditable.created_by is sufficient
          # organization field from OrganizationScoped

          content = models.TextField(_("Content"))

          # Generic relation to parent object
          content_type = models.ForeignKey(
              ContentType, verbose_name=_("Parent Type"), on_delete=models.CASCADE
          )
          object_id = models.CharField( # Use CharField for flexibility (UUIDs)
              _("Parent ID"), max_length=255, db_index=True
          )
          content_object = GenericForeignKey('content_type', 'object_id')

          # Basic Threading (Replies)
          parent = models.ForeignKey(
              'self', verbose_name=_("Parent Comment"),
              on_delete=models.CASCADE, # Delete replies if parent deleted
              null=True, blank=True, related_name='replies', db_index=True
          )

          is_edited = models.BooleanField(_("Is Edited"), default=False)
          status = models.CharField(
              _("Status"), max_length=20, choices=CommentStatus.CHOICES,
              default=CommentStatus.VISIBLE, db_index=True
          )
          attachments = models.ManyToManyField(
              FileStorage, verbose_name=_("Attachments"), blank=True, related_name="comment_attachments"
          )
          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True
          )

          class Meta:
              verbose_name = _("Comment")
              verbose_name_plural = _("Comments")
              ordering = ['created_at'] # Oldest first for threads
              indexes = [
                  models.Index(fields=["content_type", "object_id"]), # For GFK lookup
                  models.Index(fields=["status"]),
                  models.Index(fields=["parent"]),
              ]

          def __str__(self):
              # Truncate content for display
              limit = 50
              truncated_content = (self.content[:limit] + '...') if len(self.content) > limit else self.content
              return f"Comment by {self.created_by or 'System'} on {self.content_object or 'Unknown'}: '{truncated_content}'"

          # Add permission checks here if needed (e.g., can_edit, can_delete)
          # def user_can_edit(self, user): ...
          # def user_can_delete(self, user): ...
      ```
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `CommentFactory` in `api/v1/features/collaboration/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from django.contrib.contenttypes.models import ContentType
      from ..models import Comment, CommentStatus
      from api.v1.base_models.user.tests.factories import UserFactory
      from api.v1.base_models.organization.tests.factories import OrganizationFactory
      # Import a factory for a sample commentable object, e.g., Product
      # from api.v1.features.products.tests.factories import ProductFactory

      class CommentFactory(DjangoModelFactory):
          class Meta:
              model = Comment

          # user = factory.SubFactory(UserFactory) # Handled by Auditable mixin usually
          content = factory.Faker('paragraph', nb_sentences=3)
          parent = None # Set explicitly for replies

          # Needs a concrete object to attach to by default for GFK
          # Option 1: Default to a specific type (e.g., Product)
          # content_object = factory.SubFactory(ProductFactory)
          # Option 2: Pass object in test setup
          content_type = factory.LazyAttribute(lambda o: ContentType.objects.get_for_model(o.content_object) if o.content_object else None)
          object_id = factory.SelfAttribute('content_object.pk')

          status = CommentStatus.VISIBLE
          custom_fields = {}

          # Link organization (should likely come from content_object or user context)
          organization = factory.SelfAttribute('content_object.organization') # If parent is OrgScoped
          # organization = factory.SubFactory(OrganizationFactory) # Or set directly if needed

          # Handle attachments M2M post-generation if needed
          # @factory.post_generation
          # def attachments(self, create, extracted, **kwargs): ...
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances, including replies (setting `parent`) and linking to different `content_object` types.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create `api/v1/features/collaboration/admin.py`.
  [ ] Define `CommentAdmin`:
      ```python
      from django.contrib import admin
      from django.contrib.contenttypes.admin import GenericStackedInline # Or Tabular
      from .models import Comment

      @admin.register(Comment)
      class CommentAdmin(admin.ModelAdmin):
          list_display = (
              'id', 'content_type', 'object_id', 'content_object_link',
              'user_display', 'parent', 'status', 'created_at', 'is_edited'
          )
          list_filter = ('status', 'content_type', 'created_at', 'organization')
          search_fields = ('content', 'object_id', 'created_by__username')
          list_select_related = ('content_type', 'created_by', 'organization', 'parent') # Use created_by from Auditable
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by', 'content_object', 'is_edited')
          raw_id_fields = ('parent', 'content_type') # Helpful for linking
          fields = (
              'organization', ('content_type', 'object_id'), 'parent',
              'status', 'content', 'attachments', 'custom_fields',
              ('created_at', 'created_by'), ('updated_at', 'updated_by'), 'is_edited'
          )
          filter_horizontal = ('attachments',) # Better widget for M2M

          @admin.display(description='Author')
          def user_display(self, obj):
              return obj.created_by or 'System'

          @admin.display(description='Parent Object')
          def content_object_link(self, obj):
              # Link to parent object admin if possible
              if obj.content_object:
                  # ... logic to get admin URL ...
                  return obj.content_object
              return "-"

      # Optional: Inline for showing comments on parent model admin (e.g., ProductAdmin)
      # class CommentInline(GenericStackedInline): # Or GenericTabularInline
      #     model = Comment
      #     fields = ('created_by', 'content', 'status', 'attachments') # etc
      #     readonly_fields = ('created_by',)
      #     ct_field = "content_type"
      #     ct_fk_field = "object_id"
      #     extra = 0
      ```
  [ ] **(Manual Test):** Verify Admin CRUD (esp. GFK display), filtering. Test creating replies via admin.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations collaboration`.
  [ ] **Review generated migration file carefully.** Check GFK fields, FKs (`parent`, `user`), M2M (`attachments`), indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for `CommentSerializer`. Test validation (content required, parent exists and belongs to same thread), representation (user details, parent ID, attachments, custom fields), GFK handling, nested replies (optional).
  [ ] Define `CommentSerializer` in `api/v1/features/collaboration/serializers.py`. Handle nested replies if needed.
      ```python
      from rest_framework import serializers
      from django.contrib.contenttypes.models import ContentType
      from ..models import Comment, CommentStatus
      # Import User/FileStorage serializers if nesting
      # from api.v1.base_models.user.serializers import UserSummarySerializer
      # from api.v1.base_models.common.serializers import FileStorageSerializer
      # from core.serializers import FieldPermissionSerializerMixin

      class ReplySerializer(serializers.ModelSerializer): # Minimal serializer for nested replies
          # user = UserSummarySerializer(read_only=True)
          user_id = serializers.IntegerField(source='created_by_id', read_only=True) # Use Auditable field

          class Meta:
              model = Comment
              fields = ['id', 'user_id', 'content', 'is_edited', 'status', 'created_at', 'updated_at']
              read_only_fields = fields

      class CommentSerializer(serializers.ModelSerializer): # Add FieldPermissionMixin?
          # user = UserSummarySerializer(read_only=True) # Nested user info
          user_id = serializers.IntegerField(source='created_by_id', read_only=True) # Use Auditable field
          replies = ReplySerializer(many=True, read_only=True) # Show direct replies nested
          # attachments = FileStorageSerializer(many=True, read_only=True) # Nested file info
          attachment_ids = serializers.PrimaryKeyRelatedField(
              queryset=FileStorage.objects.all(), # Scope by org/permissions?
              source='attachments', many=True, write_only=True, required=False
          )
          parent_id = serializers.PrimaryKeyRelatedField(
              queryset=Comment.objects.all(), source='parent', allow_null=True, required=False, write_only=True
          )
          # Fields for writing the GFK target on create
          content_type_id = serializers.PrimaryKeyRelatedField(
              queryset=ContentType.objects.all(), write_only=True, required=True
          )
          object_id = serializers.CharField(write_only=True, required=True)

          class Meta:
              model = Comment
              fields = [
                  'id', 'user_id', #'user',
                  'content_type_id', 'object_id', # Write-only for linking
                  'parent', 'parent_id', # Read parent PK, write parent ID
                  'content', 'is_edited', 'status',
                  'attachments', 'attachment_ids', # Read nested, write IDs
                  'custom_fields',
                  'replies', # Read-only nested replies
                  'created_at', 'updated_at',
              ]
              read_only_fields = ('id', 'parent', 'is_edited', 'status', 'attachments', 'replies', 'created_at', 'updated_at', 'user_id')
              # Note: status might be updatable via specific moderation actions

          def validate(self, data):
              # Validate parent comment belongs to the same content_object if parent is set
              parent = data.get('parent')
              content_type = data.get('content_type_id') # This is the ContentType instance now
              object_id = data.get('object_id')

              if parent:
                   if parent.content_type != content_type or str(parent.object_id) != str(object_id):
                       raise serializers.ValidationError("Reply must belong to the same parent object thread.")
                   if parent.parent_id is not None: # Limit to one level of reply nesting?
                       raise serializers.ValidationError("Direct replies only; nesting deeper is not supported.")

              # Add custom_fields validation here
              # Add permission checks if needed (e.g., user can comment on target object)
              return data

          def create(self, validated_data):
              # Pop M2M fields before super().create()
              attachments_data = validated_data.pop('attachments', None)
              # GFK fields already validated/converted by PrimaryKeyRelatedField/CharField
              comment = super().create(validated_data)
              if attachments_data:
                  comment.attachments.set(attachments_data)
              return comment
          # Override update similarly if allowing edits, handle attachments M2M
      ```
  [ ] Run tests; expect pass. Refactor (especially GFK setting and nested write handling).

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/comments/` URL, authentication, Org Scoping, basic permissions. Test listing comments for a specific parent object.
  [ ] Define `CommentViewSet` in `api/v1/features/collaboration/views.py`. Inherit `OrganizationScopedViewSetMixin`. Implement filtering by parent object.
      ```python
      from rest_framework import viewsets, permissions
      from django.contrib.contenttypes.models import ContentType
      from core.views import OrganizationScopedViewSetMixin # Adjust path
      from ..models import Comment
      from ..serializers import CommentSerializer
      # Import filters, permissions

      class CommentViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
          serializer_class = CommentSerializer
          permission_classes = [permissions.IsAuthenticated] # Add specific comment permissions
          # Base queryset filtered by org via mixin
          queryset = Comment.objects.filter(status=CommentStatus.VISIBLE) \
                                    .select_related('created_by', 'parent') \
                                    .prefetch_related('replies', 'attachments')

          filter_backends = [...] # Add filtering backend (e.g., django-filter)
          # filterset_fields = ['content_type', 'object_id', 'user'] # Define FilterSet class

          def get_queryset(self):
              qs = super().get_queryset()
              # Allow filtering by parent object via query params
              parent_type_id = self.request.query_params.get('content_type_id')
              parent_object_id = self.request.query_params.get('object_id')

              if parent_type_id and parent_object_id:
                  try:
                      # Validate content_type exists?
                      # ContentType.objects.get_for_id(parent_type_id)
                      qs = qs.filter(content_type_id=parent_type_id, object_id=parent_object_id, parent__isnull=True) # Only top-level comments
                  except (ValueError, ContentType.DoesNotExist):
                      return qs.none() # Invalid type ID

              # Add permission filtering - ensure user can VIEW the parent object? Complex.
              # Rely on scoping + specific permissions for now.
              return qs

          def perform_create(self, serializer):
              # Set user from request, check permission to comment on parent object
              parent_object = None
              try:
                   ctype = ContentType.objects.get_for_id(serializer.validated_data['content_type_id'].id)
                   parent_object = ctype.get_object_for_this_type(pk=serializer.validated_data['object_id'])
              except Exception:
                   raise serializers.ValidationError("Invalid parent object specified.")

              # Example permission check (assumes view perm implies comment perm)
              if not self.request.user.has_perm(f'{ctype.app_label}.view_{ctype.model}', parent_object):
                   raise PermissionDenied("You do not have permission to comment on this object.")

              # Check parent comment validity moved to serializer validate()

              serializer.save(created_by=self.request.user) # Set author

          # Override perform_update/perform_destroy for edit/delete permissions
      ```
  [ ] Run basic tests; expect pass. Refactor (especially GFK filtering and permission checks).

  ### 3.7 URL Routing (`urls.py`)

  [ ] Create `api/v1/features/collaboration/urls.py`. Import `CommentViewSet`. Register with router: `router.register(r'comments', views.CommentViewSet)`.
  [ ] Include `collaboration.urls` in `api/v1/features/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   LIST: Test filtering by `content_type_id` & `object_id`. Verify only top-level comments returned by default. Verify nested `replies` are present. Test pagination. **Verify Org Scoping.**
      *   CREATE: Test creating top-level comments and replies (providing `parent_id`). Test associating with different parent object types. Test attachment uploads with comments. Test validation errors (missing content, invalid parent). Test permissions (can user comment on target object?).
      *   RETRIEVE (if needed, usually list is sufficient).
      *   UPDATE/PATCH: Test editing own comment (check `is_edited` flag). Test permissions.
      *   DELETE: Test deleting own comment (check status becomes HIDDEN or row deleted). Test permissions.
      *   Test moderation actions if implemented.
      *   Saving/Validating `custom_fields`.
  [ ] Implement/Refine ViewSet/Serializer logic (especially `perform_create`, permission checks, GFK handling).
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/features/collaboration`).
[ ] Manually test creating/viewing comments and replies via API client on different objects. Check attachments.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (Refine GFK validation/setting in API, single primary logic for channels, nested update logic).
[ ] Implement notification triggers for new comments/replies.
[ ] Create Pull Request.
[ ] Update API documentation.

--- END OF FILE comment_implementation_steps.md ---