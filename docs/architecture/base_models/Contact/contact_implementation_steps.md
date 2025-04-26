Okay, let's generate the implementation steps for the `Contact` model and its associated communication channel models (`ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`), based on the PRD and using the TDD checklist format.

This is more complex as it involves multiple related models and potentially nested serializers/forms for managing them together.

--- START OF FILE contact_implementation_steps.md ---

# Contact & Communication Channels - Implementation Steps

## 1. Overview

**Model Names:**
`Contact`, `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`

**Corresponding PRD:**
`contact_prd.md` (Simplified version with Custom Fields and separate communication channels)

**Depends On:**
`Timestamped`, `Auditable`, `Organization`, `Address`, `django-taggit` (if used). Also depends on `User` for Auditable FKs. Requires `FileStorage` if social profile images or other attachments are planned later, but not directly for these models. Phone number field validation library (`django-phonenumber-field`) is recommended.

**Key Features:**
Central model for individual contacts (`Contact`) with related models for storing multiple emails, phone numbers, and physical addresses. Supports linking to organizations, tagging, and custom fields.

**Primary Location(s):**
`api/v1/base_models/common/` (Assuming `common` app for shared entities)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `Organization`, `Address`) are implemented and migrated.
[ ] Ensure the `common` app structure exists (`api/v1/base_models/common/`).
[ ] Install recommended libraries: `pip install django-taggit django-phonenumber-field`.
[ ] Add `'taggit'` and `'phonenumber_field'` to `INSTALLED_APPS` in `config/settings/base.py`.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization`, `Address` exist.

## 3. Implementation Steps (TDD Workflow)

  *(Implement related channel models alongside or just after the main Contact model)*

  ### 3.1 Communication Channel Model Definitions (`models.py`)

Okay, let's generate the implementation steps for the `Contact` model and its related Communication Channel models (`ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`). This follows the simplified `Contact` PRD and uses the TDD checklist format.  [ ] **(Test First - Email)** Write Unit Tests (`tests/unit/test_models.py`) for `ContactEmailAddress`: creation, FK to Contact, unique email constraint (if desired system-wide), `is_primary` default, `__str__`.
  [ ] **(Test First - Phone)** Write Unit Tests for `ContactPhoneNumber`: creation, FK to Contact, phone number validation (using library), `is_primary` default, `__str__`.
  [ ] **(Test First - Address Link)** Write Unit Tests for `ContactAddress`: creation, FKs to Contact and Address, `is_primary` default, `__str__`.
  [ ] Define `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress` in `api/v1/base_models/common/models.py

This implementation assumes the Communication Channels are separate models linked by ForeignKey, which is the more flexible approach recommended in the PRD.

--- START OF FILE contact_implementation_steps.md ---

# Contact & Communication Channels - Implementation Steps

## 1. Overview

**Model Name(s):**
`Contact`, `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress` (potentially `ContactSocialProfile` later)

**Corresponding PRD:**
`contact_prd.md` (Simplified`:
      ```python
      # api/v1/base_models/common/models.py
      # ... (imports for Timestamped, Auditable, Contact, Address) ...
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from phonenumber_field.modelfields import PhoneNumberField # If using library

      # Assume Contact model definition comes *before* these

      class ContactEmailAddress(Timestamped, Auditable):
          # TYPE_CHOICES = ... ('Work', 'Personal', 'Other')
          contact = models.ForeignKey('Contact', on_delete=models.CASCADE, related_name='email_addresses')
          email = models.EmailField(_("Email"), unique=True, db_index=True) # System-wide unique? Discuss.
          type = models.CharField(_("Type"), max_length=20, default='Work') # Add choices=TYPE_CHOICES
          is_primary = models.BooleanField(_("Is Primary"), default=False)

          class Meta:
              verbose_name = _("Contact Email Address")
              verbose_name_plural = _("Contact Email Addresses")
              unique_together = (('contact', 'email'),) # Email unique per contact at least
              # Add constraint later to ensure only one primary per contact

          def __str__(self):
              return self.email

      class ContactPhoneNumber(Timestamped, Auditable):
          # TYPE_CHOICES = ... ('Work', 'Mobile', 'Home', 'Fax')
          contact = models.ForeignKey('Contact', on_delete=models. version with Custom Fields and related Channel models)

**Depends On:**
`Timestamped`, `Auditable`, `User` (potentially for linking), `Organization`, `Address`, `django-taggit`, `django-phonenumber-field` (Recommended).

**Key Features:**
Central model for individual contacts (`Contact`) with core details, status, tags, custom fields. Separate related models handle multiple email addresses, phone numbers, and physical addresses (linking to `Address` model), each with type and primary flags.

**Primary Location(s):**
`api/v1/base_models/common/` (Assuming `common` app)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `Organization`, `Address`, `User`) are implemented and migrated.
[ ] Ensure the `common` app structure exists (`api/v1/base_models/common/`).
[ ] Install required libraries: `pip install django-taggit django-phonenumber-field`.
[ ] Add `'taggit'` and `'phonenumber_field'` to `INSTALLED_APPS` in `config/settings/base.py`.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization`, `Address` exist.

## 3. Implementation Steps (TDD Workflow)

  *(Implement Contact first, then Communication Channel models)*

  ### 3.1 `Contact` Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py`) verifying:
      *   A `Contact` instance can be created.
      *   Fields (`first_name`, `last_name`, `title`, `organization_name`, `linked_organization`, `contact_type`, `statusCASCADE, related_name='phone_numbers')
          phone_number = PhoneNumberField(_("Phone Number"), db_index=True) # Uses library validation
          # Or: phone_number = models.CharField(_("Phone Number"), max_length=30, db_index=True)
          type = models.CharField(_("Type"), max_length=20, default='Work') # Add choices=TYPE_CHOICES
          is_primary = models.BooleanField(_("Is Primary"), default=False)

          class Meta:
              verbose_name = _("Contact Phone Number")
              verbose_name_plural = _("Contact Phone Numbers")
              unique_together = (('contact', 'phone_number'),)
              # Add constraint later for primary

          def __str__(self):
              return str(self.phone_number)

      class ContactAddress(Timestamped, Auditable):
          # TYPE_CHOICES = ... ('Work', 'Home', 'Shipping')
          contact = models.ForeignKey('Contact', on_delete=models.CASCADE, related_name='addresses')
          address = models.ForeignKey('Address', on_delete=models.CASCADE) # Cascade delete link if contact deleted
          type = models.CharField(_("Type"), max_length=20, default='Work') # Add choices=TYPE_CHOICES
          is_primary = models.BooleanField(_("Is Primary"), default=False)

          class Meta:
              verbose_name = _("Contact Address")
              verbose_name_plural = _("Contact Addresses")
              unique_together = (('contact', 'address', 'type'),) # Prevent duplicate links of same type
              # Add constraint later for primary

          def __str__(self):
              return f"{self.contact} - {self.type} ({self.address})"
      ```
  [ ] Run tests for channel models; expect pass. Refactor.
  [ ] **(Constraint)** Add database constraints (via custom migration `RunSQL` or potentially `django-db-constraints` library) OR model `save()` logic to enforce only one `is_primary=True` per contact per channel type (Email, Phone, Address). *(Deferrable but important)*.

  ### 3.2 Contact Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py`) verifying:
      *   `Contact` instance creation with required fields.
      *   FKs (`linked_organization`) work.
      *   Related names (`email_addresses`, `phone_numbers`, `addresses`) exist and are queryable.
      *   `custom_fields` default. `tags` manager exists. `__str__` works.
      *   Inherited fields exist.
      Run; expect failure.
  [ ] Define the `Contact` class in `api/v1/base_models/common/models.py` (likely *before* channel models due to FKs).
  [ ] Add inheritance: `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/common/models.py
      # ... (imports) ...
      from taggit.managers import TaggableManager
      # Assume Organization is imported

      class Contact(Timestamped, Auditable):
          # TYPE_CHOICES = ... ('Customer', 'Supplier', 'Lead')
          # STATUS_CHOICES = ... ('Active', 'Inactive')

          first_name = models.CharField(_("First Name"), max_length=100)
          last_name = models.CharField(_("Last Name"), max_length=100, db_index=True)
          title = models.CharField(_("Job Title"), max_length=100, blank=True)
          organization_name = models.CharField(
              _("Organization Name (Denormalized)"), max_length=255, blank=True,
              help_text=_("Company name if not linking to a formal Organization record.")
          )
          linked_organization = models.ForeignKey(
              Organization, # Assumes Organization imported
              verbose_name=_("Linked Organization"),
              related_name='contacts',
              on_delete=models.SET_NULL, # Keep contact if org deleted
              null=True, blank=True
          )
          contact_type = models.CharField(
              _("Contact Type"), max_length=50, blank=True, db_index=True # Add choices
          )
          status = models.CharField(
              _("Status"), max_length=20, default='Active', db_index=True # Add choices
          )
          source = models.CharField(_("Source"), max_length=100, blank=True)
          notes = models.TextField(_("Notes"), blank=True)
          tags = TaggableManager(blank=True, verbose_name=_("Tags"))
          custom_fields = models.JSONField(_("Custom Fields"), default=dict, blank=True)

          class Meta:
              verbose_name = _("Contact")
              verbose_name_plural = _("Contacts")
              ordering = ['last_name',`, `source`, `notes`, `custom_fields`) are correctly defined.
      *   Default values (`status`, `custom_fields`) are set.
      *   `linked_organization` FK works.
      *   `__str__` returns full name.
      *   Inherited fields exist.
      Run; expect failure.
  [ ] Define the `Contact` class in `api/v1/base_models/common/models.py`.
  [ ] Add inheritance: `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/common/models.py
      # ... previous imports ...
      from taggit.managers import TaggableManager
      from api.v1.base_models.organization.models import Organization # Adjust path

      class Contact(Timestamped, Auditable):
          # Define choices for status and contact_type
          TYPE_CUSTOMER = 'customer'
          TYPE_SUPPLIER = 'supplier'
          TYPE_LEAD = 'lead'
          TYPE_PARTNER = 'partner'
          TYPE_OTHER = 'other'
          CONTACT_TYPE_CHOICES = [
              (TYPE_CUSTOMER, _('Customer Contact')),
              (TYPE_SUPPLIER, _('Supplier Contact')),
              (TYPE_LEAD, _('Lead')),
              (TYPE_PARTNER, _('Partner Contact')),
              (TYPE_OTHER, _('Other')),
          ]

          STATUS_ACTIVE = 'active'
          STATUS_INACTIVE = 'inactive'
          STATUS_DO_NOT_CONTACT = 'do_not_contact'
          STATUS_CHOICES = [
              (STATUS_ACTIVE, _('Active')),
              (STATUS_INACTIVE, _('Inactive')),
              (STATUS_DO_NOT_CONTACT, _('Do Not Contact')),
          ]

          first_name = models.CharField(_("First Name"), max_length=100)
          last_name = models.CharField(_("Last Name"), max_length=100, db_index=True)
          title = models.CharField(_("Job Title"), max_length=100, blank=True)
          # Denormalized for quick display/filtering if needed
          organization_name = models.CharField(
              _("Organization Name (Text)"), max_length=255, blank=True, db_index=True
          )
          # Formal link to Organization record if it exists in the system
          linked_organization = models.ForeignKey(
              Organization,
              verbose_name=_("Linked Organization"),
              on_delete=models.SET_NULL,
              null=True,
              blank=True,
              related_name='contacts',
              help_text=_("Link to the Organization record this contact belongs to, if applicable.")
          )
          contact_type = models.CharField(
              _("Contact Type"), max_length=50, choices=CONTACT_TYPE_CHOICES,
              blank=True, db_index=True
          )
          status = models.CharField(
              _("Status"), max_length=20, choices=STATUS_CHOICES,
              default=STATUS_ACTIVE, db_index=True
          )
          source = models.CharField(
              _("Source"), max_length=100, blank=True,
              help_text=_("How the contact was acquired (e.g., Website, Trade Show).")
          )
          notes = models.TextField(_("Notes"), blank=True)
          tags = TaggableManager(blank=True, verbose_name=_("Tags"))
          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True
          )

          class Meta:
              verbose_name = _("Contact")
              verbose_name_plural = _("Contacts")
              ordering = ['last_name', 'first_name']
              indexes = [
                  models.Index(fields=['last_name', 'first_name']),
                  models.Index(fields=['organization_name']),
              ]

          def __str__(self):
              return f"{self.first_name} {self.last_name}".strip()

          def get_primary_email(self):
              # Helper method example (implement after Email model)
              primary = self.email_addresses.filter(is_primary=True).first()
              return primary.email if primary else None
          # Similar helpers for phone, address if needed
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Communication Channel Model Definitions (`models.py`)

  [ ] **(Test First - 'first_name']
              indexes = [
                  models.Index(fields=['last_name', 'first_name']),
              ]

          def __str__(self):
              return f"{self.first_name} {self.last_name}".strip()

          # Add @property methods later to easily get primary email/phone/address if needed
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.3 Factory Definitions (`tests/factories.py`)

  [ ] Define factories for `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress` in `api/v1/base_models/common/tests/factories.py`.
  [ ] Define `ContactFactory`, potentially using post-generation hooks or related factories to create associated channel records.
      ```python
      # ... (imports for other factories) ...
      from ..models import Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress

      class ContactFactory(DjangoModelFactory):
          class Meta:
              model = Contact

          first_name = factory.Faker('first_name')
          last_name = factory.Faker('last_name')
          title = factory.Faker('job')
          linked_organization = factory.SubFactory(OrganizationFactory)
          organization_name = factory.LazyAttribute(lambda o: o.linked_organization.name if o.linked_organization else factory.Faker('company'))
          status = 'Active'
          custom_fields = {}

          # Example: Create a primary email automatically
          # @factory.post_generation
          # def add_primary_email(self, create, extracted, **kwargs):
          #     if not create: return
          #     ContactEmailAddressFactory(contact=self, is_primary=True)

      class ContactEmailAddressFactory(DjangoModelFactory):
          class Meta:
              model = ContactEmailAddress

          contact = factory.SubFactory(ContactFactory)
          email = factory.LazyAttribute(lambda o: f"{o.contact.first_name}.{o.contact.last_name}{factory.fuzzy.FuzzyInteger(1,100).fuzz()}@example.com".lower())
          type = 'Work'
          is_primary = False

      class ContactPhoneNumberFactory(DjangoModelFactory):
           class Meta:
              model = ContactPhoneNumber

           contact = factory.SubFactory(ContactFactory)
           # Requires factory-boy installation with faker[phonenumber]
           phone_number = factory.Faker('phone_number')
           type = 'Work'
           is_primary = False

      class ContactAddressFactory(DjangoModelFactory):
           class Meta:
               model = ContactAddress

           contact = factory.SubFactory(ContactFactory)
           address = factory.SubFactory(AddressFactory)
           type = 'Work'
           is_primary = False
      ```
  [ ] **(Test)** Write tests ensuring factories create valid instances and relationships.

  ### 3.4 Admin Registration (`admin.py`)

  [ ] Define inlines for `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`.
  [ ] Define `ContactAdmin` using the inlines.
      ```python
      # api/v1/base_models/common/admin.py
      from django.contrib import admin
      from .models import Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress

      class ContactEmailAddressInline(admin.TabularInline):
          model = ContactEmailAddress
          extra = 1

      class ContactPhoneNumberInline(admin.TabularInline):
          model = ContactPhoneNumber
          extra = 1

      class ContactAddressInline(admin.TabularInline):
          model = ContactAddress
          extra = 1
          fields = ('address', 'type', 'is_primary') # Select fields for inline

      @admin.register(Contact)
      class ContactAdmin(admin.ModelAdmin):
          list_display = ('__str__', 'title', 'organization_name', 'linked_organization', 'contact_type', 'status')
          search_fields = ('first_name', 'last_name', 'organization_name', 'email_addresses__email', 'phone_numbers__phone_number') # Search related
          list_filter = ('contact_type', 'status', 'linked_organization')
          inlines = [ContactEmailAddressInline, ContactPhoneNumberInline, ContactAddressInline]
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          # Add fieldsets for better layout
      ```
  [ ] **(Manual Test):** Verify Admin interface for Contacts, including managing related channels inline.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review generated migration file(s) carefully.** Ensure all models (Contact, channels) and relationships are created correctly.
  [ ] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write tests for `ContactEmailAddressSerializer`, `ContactPhoneNumberSerializer`, `ContactAddressSerializer` (validation, representation). Write tests for `ContactSerializer` (validation, representation, handling nested writes for channels).
  [ ] Define serializers for communication channels first.
  [ ] Define `ContactSerializer` in `api/v1/base_models/common/serializers.py`. Handle nested serialization/writing for channels. This often requires overriding `create` and `update` or using libraries like `drf-writable-nested`.
      ```python
      # api/v1/base_models/common/serializers.py
      # ... (import models and potentially AddressSerializer) ...
      from phonenumber_field.serializerfields import PhoneNumberField # If using library
      from taggit.serializers import TagListSerializerField, TaggitSerializer

      class ContactEmailAddressSerializer(serializers.ModelSerializer):
          class Meta:
              model = ContactEmailAddress
              fields = ['id', 'email', 'type', 'is_primary']

      class ContactPhoneNumberSerializer(serializers.ModelSerializer):
          phone_number = PhoneNumberField() # Uses library validation/formatting
          class Meta:
              model = ContactPhoneNumber
              fields = ['id', 'phone_number', 'type', 'is_primary']

      class ContactAddressSerializer(serializers.ModelSerializer):
          # Potentially nest AddressSerializer for read, accept Address PK for write
          # address = AddressSerializer(read_only=True)
          address_id = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all(), source='address', write_only=True)
          class Meta:
              model = ContactAddress
              fields = ['id', 'address_id', 'address', 'type', 'is_primary']
              read_only_fields = ('address',) # Show nested on read

      class ContactSerializer(TaggitSerializer, serializers.ModelSerializer):
          tags = TagListSerializerField(required=False)
          # Nested serializers for related channels
          email_addresses = ContactEmailAddressSerializer(many=True, required=False)
          phone_numbers = ContactPhoneNumberSerializer(many=True, required=False)
          addresses = ContactAddressSerializer(many=True, required=False)
          # Add nested Org serializer if needed for reads
          # linked_organization = OrganizationSummarySerializer(read_only=True)
          # linked_organization_id = serializers.PrimaryKeyRelatedField(...) # For writes

          class Meta:
              model = Contact
              fields = [
                  'id', 'first_name', 'last_name', 'title',
                  'organization_name', 'linked_organization', # Or linked_organization_id
                  'contact_type', 'status', 'source', 'notes', 'tags',
                  'email_addresses', 'phone_numbers', 'addresses', # Nested data
                  'custom_fields', 'created_at', 'updated_at',
              ]

          # **CRUCIAL:** Implement create/update to handle nested writes
          # Example using basic loop (DRF-writable-nested simplifies this)
          def create(self, validated_data):
              emails_data = validated_data.pop('email_addresses', [])
              phones_data = validated_data.pop('phone_numbers', [])
              addresses_data = validated_data.pop('addresses', [])
              tags_data = validated_data.pop('tags', None) # Handled by TaggitSerializer

              contact = Contact.objects.create(**validated_data)

              if tags_data is not None: # TaggitSerializer needs tags set after create
                  contact.tags.set(tags_data)

              for email_data in emails_data:
                  ContactEmailAddress.objects.create(contact=contact, **email_data)
              for phone_data in phones_data:
                  ContactPhoneNumber.objects.create(contact=contact, **phone_data)
              for address_data in addresses_data:
                  ContactAddress.objects.create(contact=contact, **address_data)
              # Add logic here to enforce primary=True uniqueness if needed

              return contact

          def update(self, instance, validated_data):
              # Similar logic for update: Pop nested data, update instance,
              # then clear/recreate or update nested channel objects.
              # This is complex; drf-writable-nested is recommended.
              # Don't forget tags update: tags_data = validated_data.pop('tags', None) ... instance.tags.set()
              # Ensure custom_fields update correctly
              instance = super().update(instance, validated_data)
              # ... (update/create nested logic) ...
              return instance

          # Add validate_custom_fields method
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests for `/api/v1/contacts/` (permissions, existence).
  [ ] Define `ContactViewSet` in `api/v1/base_models/common/views.py`:
      ```python
      from rest_framework import viewsets, permissions
      from ..models import Contact
      from ..serializers import ContactSerializer
      # ... import filters, permissions ...

      class ContactViewSet(viewsets.ModelViewSet):
          serializer_class = ContactSerializer
          permission_classes = [permissions.IsAuthenticated] # Add RBAC permissions
          # queryset needs prefetching for performance with nested serializers
          queryset = Contact.objects.prefetch_related(
              'email_addresses', 'phone_numbers', 'addresses', 'tags'
          ).select_related('linked_organization').all() # Add Org Scoping later
          filter_backends = [...] # Advanced filtering, Search, Ordering
          filterset_fields = ['contact_type', 'status', 'linked_organization', 'tags__name']
          search_fields = ['first_name', 'last_name', 'organization_name', 'email_addresses__email']
          ordering_fields = ['last_name', 'first_name', 'created_at', 'updated_at']
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [ ] Import `ContactViewSet` in `api/v1/base_models/common/urls.py`.
  [ ] Register with router: `router.register(r'contacts', views.ContactViewSet)`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   LIST (with filters). Verify nested channel data present.
      *   CREATE (with nested emails/phones/addresses). Verify validation.
      *   RETRIEVE. Verify nested data.
      *   UPDATE (PUT/PATCH with changes to Contact fields and nested channels).
      *   DELETE.
      *   Permissions. Org Scoping (when added). Tagging.
      *   Saving/Validating `custom_fields`.
  [ ] Implement/Refine ViewSet and Serializer `create`/`update` logic. Ensure Field-Level permissions checked if applicable.
  [ ] Run all API tests; expect Email)** Write Unit Tests verifying `ContactEmailAddress` model: FK to Contact, `email` field (EmailField, unique?), `type` choices, `is_primary` default/logic, inheritance.
  [ ] Define `ContactEmailAddress` model in `common/models.py`.
      ```python
      class ContactEmailAddress(Timestamped, Auditable):
          CHANNEL_TYPE_WORK = 'work'
          CHANNEL_TYPE_PERSONAL = 'personal'
          CHANNEL_TYPE_OTHER = 'other'
          TYPE_CHOICES = [
              (CHANNEL_TYPE_WORK, _('Work')),
              (CHANNEL_TYPE_PERSONAL, _('Personal')),
              (CHANNEL_TYPE_OTHER, _('Other')),
          ]

          contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='email_addresses')
          email = models.EmailField(_("Email"), unique=True, db_index=True) # Unique system-wide?
          type = models.CharField(
              _("Type"), max_length=20, choices=TYPE_CHOICES, default=CHANNEL_TYPE_WORK
          )
          is_primary = models.BooleanField(_("Is Primary"), default=False, db_index=True)

          class Meta:
              verbose_name = _("Contact Email Address")
              verbose_name_plural = _("Contact Email Addresses")
              unique_together = ('contact', 'is_primary') # Can have only one primary

          def __str__(self):
              return self.email

          # Add save() method override here or signal to enforce single primary later
      ```
  [ ] Run email tests; expect pass. Refactor.
  [ ] **(Test First - Phone)** Write Unit Tests verifying `ContactPhoneNumber` model: FK, `phone_number` field (using `PhoneNumberField`), `type`, `is_primary`, inheritance.
  [ ] Define `ContactPhoneNumber` model.
      ```python
      from phonenumber_field.modelfields import PhoneNumberField

      class ContactPhoneNumber(Timestamped, Auditable):
          # Define TYPE_CHOICES (Work, Mobile, Home, Fax...)
          CHANNEL_TYPE_WORK = 'work'
          CHANNEL_TYPE_MOBILE = 'mobile'
          # ... other types ...
          TYPE_CHOICES = [...]

          contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='phone_numbers')
          phone_number = PhoneNumberField(_("Phone Number"), unique=True, db_index=True) # Unique system-wide?
          type = models.CharField(
              _("Type"), max_length=20, choices=TYPE_CHOICES, default=CHANNEL_TYPE_WORK
          )
          is_primary = models.BooleanField(_("Is Primary"), default=False, db_index=True)

          class Meta:
              verbose_name = _("Contact Phone Number")
              verbose_name_plural = _("Contact Phone Numbers")
              unique_together = ('contact', 'is_primary')

          def __str__(self):
              return str(self.phone_number)
      ```
  [ ] Run phone tests; expect pass. Refactor.
  [ ] **(Test First - Address Link)** Write Unit Tests verifying `ContactAddress` model: FKs to Contact and Address, `type`, `is_primary`, inheritance.
  [ ] Define `ContactAddress` model.
      ```python
      class ContactAddress(Timestamped, Auditable):
          # Define TYPE_CHOICES (Work, Home, Billing, Shipping...)
          CHANNEL_TYPE_WORK = 'work'
          CHANNEL_TYPE_HOME = 'home'
          # ... other types ...
          TYPE_CHOICES = [...]

          contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='addresses')
          address = models.ForeignKey(Address, on_delete=models.CASCADE) # Cascade OK: link dies if contact or address dies
          type = models.CharField(
              _("Type"), max_length=20, choices=TYPE_CHOICES, default=CHANNEL_TYPE_WORK
          )
          is_primary = models.BooleanField(_("Is Primary"), default=False, db_index=True)

          class Meta:
              verbose_name = _("Contact Address")
              verbose_name_plural = _("Contact Addresses")
              unique_together = (('contact', 'address'), ('contact', 'is_primary')) # Only one primary link per contact

          def __str__(self):
              return f"{self.contact}: {self.type} @ {self.address_id}"
      ```
  [ ] Run address link tests; expect pass. Refactor.

  ### 3.3 Single Primary Logic (Model `save` or Signal)

  [ ] **(Test First)** Write Integration Tests ensuring that setting `is_primary=True` on one `ContactEmailAddress` automatically sets `is_primary=False` on all *other* email addresses for the *same* contact. Repeat for Phone and Address models.
  [ ] Implement the logic. Recommended: Override `save()` method on `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`.
      ```python
      # Example for ContactEmailAddress.save()
      def save(self, *args, **kwargs):
          if self.is_primary:
              # Set other email addresses for this contact to is_primary=False
              ContactEmailAddress.objects.filter(
                  contact=self.contact, is_primary=True
              ).exclude(pk=self.pk).update(is_primary=False)
          super().save(*args, **kwargs)
          # Optional: Ensure at least one primary exists if required by business logic
          # if not self.contact.email_addresses.filter(is_primary=True).exists():
          #    self.is_primary = True # Make this one primary if none exist (careful with loops)
          #    super().save(update_fields=['is_primary']) # Save again only this field
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.4 Factory Definitions (`tests/factories.py`)

  [ ] Define factories for `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`.
      ```python
      class ContactFactory(DjangoModelFactory): # Define ContactFactory first
          class Meta:
              model = Contact
              # django_get_or_create = ? Need a good unique identifier

          first_name = factory.Faker('first_name')
          last_name = factory.Faker('last_name')
          organization_name = factory.Faker('company')
          # linked_organization = factory.SubFactory(OrganizationFactory)
          status = Contact.STATUS_ACTIVE
          # ... other fields ...

      class ContactEmailAddressFactory(DjangoModelFactory):
          class Meta:
              model = ContactEmailAddress
              django_get_or_create = ('email',) # If email is unique

          contact = factory.SubFactory(ContactFactory)
          email = factory.LazyAttribute(lambda o: f"{o.contact.first_name}.{o.contact.last_name}{factory.fuzzy.FuzzyInteger(1,99).fuzz()}@example.com")
          type = ContactEmailAddress.CHANNEL_TYPE_WORK
          is_primary = False

      class ContactPhoneNumberFactory(DjangoModelFactory):
           class Meta:
               model = ContactPhoneNumber
               # django_get_or_create = ('phone_number',) # If phone is unique & using lib

           contact = factory.SubFactory(ContactFactory)
           phone_number = factory.Faker('phone_number') # Adjust if using PhoneNumberField factory integration
           type = ContactPhoneNumber.CHANNEL_TYPE_WORK
           is_primary = False

      class ContactAddressFactory(DjangoModelFactory):
           class Meta:
               model = ContactAddress

           contact = factory.SubFactory(ContactFactory)
           address = factory.SubFactory(AddressFactory)
           type = ContactAddress.CHANNEL_TYPE_WORK
           is_primary = False
      ```
  [ ] **(Test)** Write simple tests ensuring factories create valid instances.

  ### 3.5 Admin Registration (`admin.py`)

  [ ] Define `InlineModelAdmin` classes for `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`.
  [ ] Define `ContactAdmin` including the inlines.
      ```python
      # api/v1/base_models/common/admin.py
      # ... other imports ...
      from .models import Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress

      class ContactEmailAddressInline(admin.TabularInline):
          model = ContactEmailAddress
          extra = 1

      class ContactPhoneNumberInline(admin.TabularInline):
          model = ContactPhoneNumber
          extra = 1

      class ContactAddressInline(admin.TabularInline):
          model = ContactAddress
          extra = 1
          fields = ('address', 'type', 'is_primary') # Select fields for inline

      @admin.register(Contact)
      class ContactAdmin(admin.ModelAdmin):
          list_display = (
              '__str__', 'organization_name', 'contact_type', 'status',
              'get_primary_email', 'get_primary_phone' # Example custom methods
          )
          search_fields = ('first_name', 'last_name', 'organization_name', 'email_addresses__email', 'phone_numbers__phone_number')
          list_filter = ('status', 'contact_type', 'linked_organization')
          inlines = [
              ContactEmailAddressInline,
              ContactPhoneNumberInline,
              ContactAddressInline,
          ]
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          # Add fieldsets, filter_horizontal for tags if needed

          # Optimize query for related primary lookups used in list_display
          def get_queryset(self, request):
              qs = super().get_queryset(request)
              # Add prefetch for primary email/phone if using helper methods
              return qs

          # Example display methods
          # @admin.display(description='Primary Email')
          # def get_primary_email(self, obj): return obj.get_primary_email()
          # @admin.display(description='Primary Phone')
          # def get_primary_phone(self, obj): return obj.get_primary_phone()
      ```
  [ ] **(Manual Test):** Verify Admin interface for Contacts, including managing emails/phones/addresses inline.

  ### 3.6 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review generated migration file(s) carefully.** Check all new models, FKs, unique constraints, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.7 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for `ContactSerializer` and potentially separate serializers for channel models if needed for nested writes. Test validation, representation (including nested channels), custom field handling, primary flag logic enforcement.
  [ ] Define Serializers in `api/v1/base_models/common/serializers.py`:
      ```python
      # Example structure - might need refinement based on write needs
      from ..models import Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress

      class ContactEmailSerializer(serializers.ModelSerializer):
           class Meta: model = ContactEmailAddress; fields = ['id', 'email', 'type', 'is_primary']

      class ContactPhoneSerializer(serializers.ModelSerializer):
           # Use PhoneNumberField from drf-phonenumber-field if using that lib
           # phone_number = PhoneNumberField()
           class Meta: model = ContactPhoneNumber; fields = ['id', 'phone_number', 'type', 'is_primary']

      class ContactAddressSerializer(serializers.ModelSerializer):
           # Nest Address details (read-only recommended for list/retrieve)
           address = AddressSerializer(read_only=True) # Assumes AddressSerializer exists
           address_id = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all(), source='address', write_only=True, required=False)

           class Meta: model = ContactAddress; fields = ['id', 'address', 'address_id', 'type', 'is_primary']

      class ContactSerializer(T pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common`). Review uncovered lines.
[ ] Manually test via API client and Django Admin, focusing on creating/editing contacts with multiple communication channels.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (e.g., primary flag enforcement, nested update logic refinement).
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure models needing a contact reference (e.g., Organization) add the `ForeignKey` correctly.

--- END OF FILE contact_implementation_steps.md ---