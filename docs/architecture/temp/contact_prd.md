# Contact Model - Product Requirements Document (PRD) - Simplified (with Custom Fields)

## 1. Overview

*   **Purpose**: To define a centralized model for storing information about **individual people** (contacts), potentially extended with **dynamic custom fields**, relevant to the ERP system.
*   **Scope**: Definition of the `Contact` data model, its core attributes, links to communication channels, relationships with Organizations, and custom field capability. Excludes interaction history and complex relationships.
*   **Implementation**: Defined as a concrete Django Model. Inherits `Timestamped`, `Auditable`. Uses a `JSONField` for custom fields. Related models for communication channels.
*   **Target Users**: Sales, Procurement, Support Teams, Admins.

## 2. Business Requirements

*   Centralized contact info for individuals.
*   Represent different types of external contacts.
*   Link contacts to Organizations.
*   Manage multiple communication methods.
*   Allow adding specific, dynamic attributes to contacts (via Custom Fields).
*   Foundation for CRM/Communication features.

## 3. Functional Requirements

### 3.1 `Contact` Model Definition
*   **Inheritance**: Inherit `Timestamped`, `Auditable`.
*   **Fields**:
    *   `first_name`, `last_name`, `title`.
    *   `organization_name` (CharField, denormalized).
    *   `linked_organization` (ForeignKey to `Organization`, SET_NULL, nullable, blank).
    *   `contact_type` (CharField w/ choices).
    *   `status` (CharField w/ choices).
    *   `source` (CharField, blank).
    *   `notes` (TextField, blank).
    *   `tags` (TaggableManager, blank).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to contacts.
*   **Meta**: `verbose_name`, `plural`, `ordering`, indexes.
*   **String Representation**: Full name.

### 3.2 Communication Channel Models (Separate Related Models)
*   Required separate models: `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress` (linking to `Address`), optional `ContactSocialProfile`.
*   Each linked via ForeignKey to `Contact`.
*   Each includes `type` (Work/Home) and `is_primary` (Boolean) fields.
*   Each inherits `Timestamped`/`Auditable`.

### 3.3 Custom Field Schema Definition (External Mechanism)
*   **Requirement**: A separate mechanism (e.g., `CustomFieldDefinition` model) is needed to define the schema for custom fields applicable to `Contact`.
*   **Schema Attributes**: Defines key, label, type, validation, choices, etc.

### 3.4 Contact Management Operations
*   **CRUD**: Standard operations for `Contact` and related communication channels (Admin/API).
*   **Inline Editing**: Manage communication channels inline in Contact admin.
*   **Primary Flag Logic**: Enforce single primary per type per contact.
*   **Custom Field Value Management**: API/Admin to view/update `custom_fields` JSON object.

### 3.5 Validation
*   Standard field validation. Email/Phone format validation (on channel models). Custom field validation against schema (in Serializer/Form). *Duplicate detection is separate.*

### 3.6 Custom Field Validation
*   **Requirement**: Data saved to `Contact.custom_fields` must be validated against the corresponding schema.
*   **Implementation**: Logic in API Serializers or Forms.

### 3.7 Out of Scope for this Model/PRD
*   Contact-Contact relationships, Interaction History (use separate Activity/Log systems), User model duplication.

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields + JSONField. Appropriate types for channels.
*   Indexing: Key Contact fields (`last_name`, `linked_organization`, `status`, `type`). Communication channel FKs, `is_primary`. Email if unique. **Requires DB support (e.g., GIN index) for efficient querying on `custom_fields`**.
*   Search: API filtering on key fields + potentially primary channel + custom fields.

### 4.2 Security
*   Access Control: Permissions (`add_contact`, etc.). Access possibly scoped by Org or role. PII handling. Custom field access control.
*   Audit Logging: Log CRUD on Contact/Channels, including `custom_fields` changes, via Audit System.

### 4.3 Performance
*   Efficient contact queries. Efficient retrieval of primary channels (`prefetch_related`). Efficient querying on `custom_fields` (needs indexing).

### 4.4 Integration
*   Core data for CRM/Sales/Support. Links to `Organization`, `Address`. Linked from channel models.
*   API Endpoints for Contact and related channels. Define `custom_fields` handling.
*   Integrates with `CustomFieldDefinition` mechanism.
*   Optional external sync.

## 5. Non-Functional Requirements

*   Scalability (millions of contacts), Availability, Consistency (incl. primary flags), Backup/Recovery.

## 6. Success Metrics

*   Data accuracy/completeness. Ease of management. Successful integration. Compliance. Successful use of custom fields.

## 7. API Documentation Requirements

*   Document Contact/Channel models/fields (incl. `custom_fields`).
*   Document APIs for managing Contact and Channels, including `custom_fields`.
*   Examples for creating contacts with channels, `custom_fields`.
*   Permissions documentation.
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   Unit Tests (Models, primary flag logic, custom field validation logic).
*   Integration Tests (API CRUD for Contact/Channels, **saving/validating `custom_fields`**, filtering, permissions, org linking).
*   Data Validation Tests (Email/Phone formats).
*   Security Tests (PII access, custom field access).

## 9. Deployment Requirements

*   Migrations (Contact, Channels, indexes incl. JSONField if needed).
*   Initial data import considerations.
*   Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Backups. Data cleansing/deduplication processes (separate).
*   Management of custom field schemas.
