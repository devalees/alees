*(Adding clarifications, especially regarding the optional Organization link)*

# Contact Model - Product Requirements Document (PRD) - Simplified (with Custom Fields)

## 1. Overview

*   **Purpose**: To define a centralized model for storing information about **individual people** (contacts), potentially extended with **dynamic custom fields**, relevant to the ERP system. This model serves as the primary repository for contact details independent of user accounts.
*   **Scope**: Definition of the `Contact` data model, its core attributes, links to communication channels (Email, Phone, Address), **optional** relationship to a primary `Organization`, and custom field capability. Excludes interaction history and complex multi-organizational relationships for a single contact record (which might require separate linking models).
*   **Implementation**: Defined as a concrete Django Model. Inherits `Timestamped`, `Auditable`. Uses a `JSONField` for custom fields. Related models for communication channels.
*   **Target Users**: Sales, Procurement, Support Teams, Admins, any module needing to reference external individuals.

## 2. Business Requirements

*   **Centralized Contact Info**: Maintain a single record for external individuals containing names, job roles, and communication details.
*   **Represent Different Types**: Classify contacts (e.g., 'Primary', 'Billing', 'Technical').
*   **Optional Primary Organization Link**: Allow associating a contact with one primary `Organization` (e.g., their employer), but this link is **not mandatory**.
*   **Manage Multiple Communication Methods**: Store multiple email addresses, phone numbers, and physical addresses per contact, with flags for primary methods.
*   **Flexibility**: Allow adding specific, dynamic attributes to contacts (via Custom Fields).
*   **Foundation for CRM/Communication**: Provide core data for CRM, sales, procurement, and support interactions.

## 3. Functional Requirements

### 3.1 `Contact` Model Definition
*   **Inheritance**: Inherit `Timestamped`, `Auditable`.
*   **Fields**:
    *   `first_name`: (CharField, max_length=100).
    *   `last_name`: (CharField, max_length=100, db_index=True).
    *   `title`: (CharField, max_length=100, blank=True) (e.g., Job Title).
    *   `organization_name`: (CharField, max_length=255, blank=True) Denormalized company name, useful if not formally linking to an `Organization` record.
    *   `linked_organization`: (**ForeignKey to `Organization`**, `on_delete=models.SET_NULL`, **`null=True`, `blank=True`**, related_name='contacts') Optional link to the primary associated Organization record.
    *   `contact_type`: (CharField with choices, blank=True) Classification (e.g., 'PRIMARY', 'BILLING', 'SUPPORT', 'TECHNICAL').
    *   `status`: (CharField with choices, default='active') Status (e.g., 'Active', 'Inactive', 'Do Not Contact'). References slugs from `Status` model.
    *   `source`: (CharField, max_length=100, blank=True) How the contact was acquired (e.g., 'Website', 'Referral', 'Conference').
    *   `notes`: (TextField, blank=True) General notes about the contact.
    *   `tags`: (TaggableManager via `django-taggit`, blank=True) For flexible categorization.
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to contacts.
*   **Meta**: `verbose_name`, `plural`, `ordering` (e.g., `['last_name', 'first_name']`), appropriate indexes.
*   **String Representation**: Full name (`first_name` `last_name`).

### 3.2 Communication Channel Models (Separate Related Models)
*   Required separate models: `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress` (linking to `Address`). Optional `ContactSocialProfile`.
*   Each linked via **required** ForeignKey to `Contact`.
*   Each includes `type` (Work/Home/Other) and `is_primary` (BooleanField) fields.
*   Each inherits `Timestamped`/`Auditable`.
*   Logic (e.g., model `save` override) required to ensure only one `is_primary` is True per `type` per `Contact` for each channel type.

### 3.3 Custom Field Schema Definition (External Mechanism)
*   **Requirement**: A separate mechanism (e.g., `CustomFieldDefinition` model, filtered by a 'Contact' context) is needed to define the schema for custom fields applicable to `Contact`.
*   **Schema Attributes**: Defines key, label, type, validation, choices, etc.

### 3.4 Contact Management Operations
*   **CRUD**: Standard operations for `Contact` and related communication channels (Admin/API). Ability to set/unset the optional `linked_organization`.
*   **Inline Editing**: Manage communication channels inline in Contact admin.
*   **Primary Flag Logic**: System enforces single primary per type per contact (as defined in 3.2).
*   **Custom Field Value Management**: API/Admin to view/update `custom_fields` JSON object, validating against the defined schema.

### 3.5 Validation
*   Required fields (`first_name`, `last_name`). Email/Phone format validation (on channel models). Custom field validation against schema (in Serializer/Form). Ensure `linked_organization` (if provided) points to a valid Organization PK. *Duplicate detection is a separate feature.*

### 3.6 Out of Scope for this Model/PRD
*   Contact-Contact relationships, Interaction History (use separate Activity/Log systems), linking a single Contact to *multiple* Organizations simultaneously (would require M2M), User model duplication.

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields + JSONField. Separate tables for channels. Appropriate types for channels (EmailField, PhoneNumberField).
*   Indexing: Key Contact fields (`last_name`, `linked_organization`, `status`, `type`). Communication channel FKs, `is_primary`. Email field in `ContactEmailAddress`. **Requires DB support (e.g., GIN index) for efficient querying on `custom_fields`**.
*   Search: API filtering on key fields + potentially primary channel + custom fields.

### 4.2 Security
*   Access Control: Permissions (`add_contact`, `change_contact`, etc.). Access possibly scoped by Org (if Contacts become org-scoped later, TBD) or role. PII handling. Custom field access control.
*   Audit Logging: Log CRUD on Contact/Channels, including `custom_fields` changes and changes to `linked_organization`, via Audit System.

### 4.3 Performance
*   Efficient contact queries. Efficient retrieval of primary channels (`prefetch_related`). Efficient querying on `custom_fields` (needs indexing).

### 4.4 Integration
*   Core data for CRM/Sales/Support. Links *to* `Organization` (optional), `Address`. Linked *from* channel models. Referenced by `Organization.primary_contact` (optional).
*   API Endpoints for Contact and related channels. Define `custom_fields` handling. Define handling of optional `linked_organization`.
*   Integrates with `CustomFieldDefinition` mechanism.
*   Optional external sync (e.g., CRM).

## 5. Non-Functional Requirements

*   Scalability (millions of contacts), Availability, Consistency (incl. primary flags), Backup/Recovery.

## 6. Success Metrics

*   Data accuracy/completeness. Ease of management. Successful integration. Compliance. Successful use of custom fields. Ability to optionally link to Organizations.

## 7. API Documentation Requirements

*   Document Contact/Channel models/fields (incl. `custom_fields`, optional `linked_organization`).
*   Document APIs for managing Contact and Channels, including how to provide/update nested channels and the optional `linked_organization_id`.
*   Document how `custom_fields` are handled.
*   Examples for creating contacts with channels, `custom_fields`, with/without organization link.
*   Permissions documentation.
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   Unit Tests (Models, primary flag logic, custom field validation logic).
*   Integration Tests (API CRUD for Contact/Channels, **saving/validating `custom_fields`**, filtering, permissions, setting/unsetting `linked_organization`). Test primary flag enforcement via nested API creates/updates.
*   Data Validation Tests (Email/Phone formats).
*   Security Tests (PII access, custom field access).

## 9. Deployment Requirements

*   Migrations (Contact, Channels, indexes incl. JSONField if needed). Ensure `linked_organization_id` column is nullable.
*   Initial data import considerations.
*   Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Backups. Data cleansing/deduplication processes (separate).
*   Management of custom field schemas.
