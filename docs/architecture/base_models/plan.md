# Base Models Classification

## 1. Core Foundation Models
- **Organization/** - Base organization structure
- **User/** - User management
- **Contact/** - Contact information
- **Address/** - Address management
- **OrganizationScoped/** - Mixin/Abstract Model for Organization scoping (requires enforcement logic)
- **OrganizationType/** - Types of organizations (Implicitly needed for Organization)

## 2. Business Domain Models
- **Product/** - Product management
- **Category/** - Product categorization
- **Warehouse/** - Inventory management
- **Tax/** - Tax management
- **UoM/** - Unit of Measurement
- **Currency/** - Currency management

## 3. System Infrastructure Models
- **Audit/** - Historical Audit Logging System (e.g., AuditLog model)
- **Status/** - Status tracking
- **VersionControl/** - Version control
- **Workflow/** - Workflow management
- **Timestamped/** - Mixin/Abstract Model for `created_at`, `updated_at`
- **Auditable/** - Mixin/Abstract Model for `created_by`, `updated_by`
- **Permission/** - Permission management

## 4. Data Management Models
- **FileStorage/** - File storage
- **DocumentSystem/** - Document management
- **Search/** - Search functionality
- **Caching/** - Caching system
- **Filtering/** - Data filtering (User-driven, e.g., via query parameters)
- **Validation/** - Data validation (Framework/Logic)

## 5. Integration & Communication Models
- **Integration/** - System integration
- **Localization/** - Internationalization
- **Notification/** - Notification system
- **Comment/** - Comment system
- **Tagging/** - Tagging system
- **Chat/** - Real-time chat system
- **VideoMeeting/** - Video conferencing system

## 6. Analytics & Reporting Models
- **Analytics/** - Analytics
- **Reporting/** - Reporting
- **ExportImport/** - Data export/import
- **Monitoring/** - System monitoring

## 7. Automation Models
- **Automation/** - Automation
- **Scheduling/** - Task scheduling

## Model Relationships

```mermaid
graph TD
    %% Core Foundation Models
    A1[Organization] --> A2[User]
    A1 --> A3[Contact]
    A1 --> A4[Address]
    A1 --> A5[OrganizationScoped] %% Structural Dependency
    A1 --> A6[OrganizationType]

    %% Business Domain Models
    B1[Product] --> B2[Category]
    B1 --> B3[Warehouse]
    B1 --> B4[Tax]
    B1 --> B5[UoM]
    A1 --> B6[Currency] %% Organization depends on Currency

    %% System Infrastructure Models
    C1[Audit System] --> C2[Status]
    C1 --> C3[VersionControl]
    C1 --> C4[Workflow]
    C5[Timestamped Mixin] %% Structural Dependency via Inheritance
    C7[Auditable Mixin] %% Structural Dependency via Inheritance (Requires User A2)
    C6[Permission]

    %% Data Management Models
    D1[FileStorage] --> D2[DocumentSystem]
    D1 --> D3[Search]
    D1 --> D4[Caching]
    %% D5[Filtering] doesn't directly depend structurally, it's applied at the API/Query layer
    %% D6[Validation] is a framework/logic applied during data operations

    %% Integration & Communication Models
    E1[Integration] --> E2[Localization]
    E1 --> E3[Notification]
    E1 --> E4[Comment]
    E1 --> E5[Tagging]
    E1 --> E6[Chat]
    E1 --> E7[VideoMeeting]

    %% Analytics & Reporting Models
    F1[Analytics] --> F2[Reporting]
    F1 --> F3[ExportImport]
    F1 --> F4[Monitoring]

    %% Automation Models
    G1[Automation] --> G2[Scheduling]

    %% Cross-Category Dependencies / Usage (Conceptual)
    A1 --> B1 %% Org owns/scopes Products
    A1 -- Logs To --> C1 %% Org changes logged in Audit System
    A1 --> D1 %% Org context for Files
    A1 --> E1 %% Org context for Integrations/Comms
    A1 --> F1 %% Org context for Analytics
    A1 --> G1 %% Org context for Automation

    A5 -- Inherited By --> B1 %% Product is OrgScoped
    A5 -- Inherited By --> B3 %% Warehouse is OrgScoped
    A5 -- Inherited By --> D2 %% Document is OrgScoped (likely)
    %% ... Many other models likely inherit OrganizationScoped

    C5 -- Inherited By --> A1 %% Org has Timestamps
    C5 -- Inherited By --> A2 %% User has Timestamps
    C5 -- Inherited By --> B1 %% Product has Timestamps
    %% ... Many other models likely inherit Timestamped

    C7 -- Inherited By --> A1 %% Org has created_by/updated_by
    C7 -- Inherited By --> A3 %% Contact has created_by/updated_by
    C7 -- Inherited By --> B1 %% Product has created_by/updated_by
    %% ... Many other models likely inherit Auditable

    A2 --> C7 %% Auditable Mixin depends on User for FKs

    B1 -- Logs To --> C1 %% Product changes logged in Audit System
    D1 -- Logs To --> C1 %% File changes logged in Audit System
    E1 -- Logs To --> C1 %% Comm changes logged in Audit System
    F1 -- Logs To --> C1 %% Analytics Config changes logged in Audit System
    G1 -- Logs To --> C1 %% Automation Rule changes logged in Audit System

    C6 --> A2 %% Permissions assigned to Users/Roles
    C6 -- Applied To --> B1 %% Permissions control access to Products
    C6 -- Applied To --> D1 %% Permissions control access to Files
    %% ... Permissions applied across many models/actions

    D5 -- Applied To --> B1 %% Filtering applied to Products API
    D5 -- Applied To --> A2 %% Filtering applied to Users API
    %% ... Filtering applied across many API endpoints

    D6 -- Applied To --> A1 %% Validation applied to Org data
    D6 -- Applied To --> A2 %% Validation applied to User data
    %% ... Validation applied across many models/serializers

    B1 --> E1 %% Product data might trigger Integrations/Notifications
    B1 --> F1 %% Product data feeds Analytics
    B1 --> G1 %% Product events might trigger Automation

    E1 --> F1 %% Integration data feeds Analytics
    E1 --> G1 %% Integration events might trigger Automation

    F1 --> G1 %% Analytics might trigger Automation

    %% Chat and VideoMeeting Dependencies
    E6[Chat] --> A1
    E6 --> A2
    E6 --> D1 %% Chat can have File Attachments
    E6 -- Logs To --> C1 %% Audit Chat events
    E6 --> C6 %% Permissions for Chat

    E7[VideoMeeting] --> A1
    E7 --> A2
    E7 --> D1 %% Meeting recordings/files
    E7 -- Logs To --> C1 %% Audit Meeting events
    E7 --> C6 %% Permissions for Meetings
    E7 --> E6 %% Potential link between chat and meetings
```
*Note: Mermaid diagram distinguishes between Mixins (`Timestamped`, `Auditable`) providing fields via inheritance and the full `Audit System` which logs historical changes.*

## Implementation Order *(Revised based on Mixin Dependencies)*

1.  **Phase 1: Core Foundational Entities, Tracking & Scoping**
    *   **Goal:** Establish minimal independent entities, user identity, base data types, essential tracking fields (timestamps, user tracking via mixins), the Organization model, and the foundational scoping mechanism.
    *   **Models/Concepts (Revised Order):**
        1.  `Timestamped/` (System Infrastructure) - **Define Mixin** (`created_at`, `updated_at`). (No external dependencies).
        2.  `Audit/` (System Infrastructure) - **Define Mixin** (`created_by`, `updated_by` - Requires `User` FK).
        3.  `User/` (Core Foundation) - Implement Authentication (Minimal dependencies).
        4.  `Currency/` (Business Domain) - Define model, **inherit Timestamped/Auditable**.
        5.  `Contact/` (Core Foundation) - Define model, **inherit Timestamped/Auditable**.
        6.  `Address/` (Core Foundation) - Define model, **inherit Timestamped/Auditable**.
        7.  `OrganizationType/` (Part of Organization Structure) - Define model, **inherit Timestamped/Auditable**.
        8.  `Organization/` (Core Foundation) - Define model, **inherit Timestamped/Auditable**, include FKs to `OrganizationType`, `Contact`, `Address`, `Currency`.
        9.  `Permission/` (System Infrastructure) - Define Roles/Groups structure, basic permission checks framework (Depends on `User`).
        10. `OrganizationScoped/` (Core Foundation) - **Define Mixin** (Depends on `Organization`).
        11. **Implement Automatic Organization Scoping Logic** - Add the *enforcement* mechanism (Depends on `OrganizationScoped` Mixin, `User`, Base API Views).

2.  **Phase 2: System Infrastructure & Other Base Data**
    *   **Goal:** Implement further system functionalities (like historical audit logging) and remaining fundamental business data types.
    *   **Models/Concepts:**
        12. `Status/` (System Infrastructure) - Generic status tracking.
        13. `Audit/` (System Infrastructure) - **Implement the historical Audit Logging system** (e.g., `AuditLog` model, logging mechanisms/signals). This system logs changes to models created in Phase 1 (which already have basic `Auditable` fields).
        14. `Validation/` (Data Management) - Establish framework for data validation.
        15. `Filtering/` (Data Management) - Implement user-driven filtering framework (e.g., `django-filter`).
        16. `UoM/` (Business Domain) - Unit of Measurement (Foundational for products/inventory).
        17. `Localization/` (Integration & Communication) - Framework for i18n/l10n if needed.

3.  **Phase 3: Core Business Logic - Products & Inventory**
    *   **Goal:** Implement the central product catalog and basic inventory concepts.
    *   **Models:**
        18. `Category/` (Business Domain) - Inherit Timestamped/Auditable.
        19. `Tax/` (Business Domain) - Inherit Timestamped/Auditable. Might depend on `Address`/Region.
        20. `Product/` (Business Domain) - Inherits `OrganizationScoped`, `Timestamped`, `Auditable`. Depends on `Category`, `UoM`, `Currency`, `Tax`. Needs linking to `Status`. Logs to `Audit`.
        21. `Warehouse/` (Business Domain) - Inherits `OrganizationScoped`, `Timestamped`, `Auditable`. Depends on `Address`.

4.  **Phase 4: Data Handling & Enhanced Infrastructure**
    *   **Goal:** Add capabilities for managing files, documents, and more complex system behaviors.
    *   **Models:**
        22. `FileStorage/` (Data Management) - Base file upload mechanism, inherit Timestamped/Auditable.
        23. `DocumentSystem/` (Data Management) - Builds on `FileStorage`. Inherits `OrganizationScoped`, `Timestamped`, `Auditable`. Depends on `User`.
        24. `Workflow/` (System Infrastructure) - State machines. Depends on `Status`.

5.  **Phase 5: Communication & Collaboration**
    *   **Goal:** Add features for user interaction, notifications, and external system links.
    *   **Models:**
        26. `Notification/` (Integration & Communication) - Inherit Timestamped/Auditable. Depends on `User`.
        27. `Comment/` (Integration & Communication) - Inherit Timestamped/Auditable. Depends on `User`, related models.
        28. `Tagging/` (Integration & Communication) - Setup `django-taggit` library (if not done for Org). Tagging relationship itself doesn't need own model usually.
        29. `Integration/` (Integration & Communication) - Framework for external connections.

6.  **Phase 6: Advanced Features & Analytics**
    *   **Goal:** Implement features for searching, performance, real-time communication, reporting, and automation.
    *   **Models:**
        30. `Search/` (Data Management) - Integrate search engine (e.g., Elasticsearch).
        31. `Caching/` (Data Management) - Implement caching strategies.
        32. `Chat/` (Integration & Communication) - Models for Chat Messages, Channels etc. Inherit necessary mixins. Depends on `User`, `Organization`, `FileStorage`, `Permissions`. Logs to `Audit`.
        33. `VideoMeeting/` (Integration & Communication) - Models for Meetings, Participants. Inherit necessary mixins. Depends on `User`, `Organization`, `FileStorage`, `Permissions`. Logs to `Audit`.
        34. `Analytics/` (Analytics & Reporting) - Data collection framework/models.
        35. `Reporting/` (Analytics & Reporting) - Report generation logic/models.
        36. `ExportImport/` (Analytics & Reporting) - Bulk data operations logic/models.
        37. `Monitoring/` (Analytics & Reporting) - System health checks integration.

7.  **Phase 7: Automation**
    *   **Goal:** Implement process automation and scheduling.
    *   **Models:**
        38. `Automation/` (Automation) - Rule engine/framework/models.
        39. `Scheduling/` (Automation) - Task scheduler integration (e.g., Celery Beat).

## Key Integration Points

### Core Foundation Integration
- Dependency Management: Core models implemented before dependent models.
- Organization definition and hierarchy.
- Automatic queryset scoping based on user organization (`OrganizationScoped` logic).
- User authentication and authorization (`Permission`).
- Contact and address management linkage.

### System Infrastructure Integration
- **Basic Tracking**: `Timestamped` and `Auditable` mixins applied consistently across models from creation.
- **Historical Logging**: `Audit` system logs significant changes to key models.
- Status tracking for core business entities (`Status`).
- Version control for specific models (`VersionControl`).
- Workflow management for business processes (`Workflow`).
- Permission control (RBAC) applied consistently (`Permission`).

### Data Management Integration
- File storage and retrieval used by Documents, Chat, etc (`FileStorage`).
- Document management system linking files to business context (`DocumentSystem`).
- Search functionality across relevant models (`Search`).
- Caching system for performance optimization (`Caching`).
- User-driven data filtering via API query parameters (`Filtering` module).
- Validation rules enforced at API/Serializer level (`Validation`).

### Business Domain Integration
- Product catalog management (`Product`, `Category`, `UoM`, `Currency`, `Tax`).
- Warehouse and inventory location management (`Warehouse`).

### Communication Integration
- Framework for external system `Integration`.
- `Localization` support.
- User `Notification` system.
- `Comment` system on various entities.
- `Tagging` system for categorization/search.
- Real-time `Chat` system.
- `VideoMeeting` capabilities.

### Analytics Integration
- `Analytics` data collection from various modules.
- `Reporting` generation based on collected data.
- `ExportImport` functionality for data transfer.
- System `Monitoring` integration.

### Automation Integration
- `Automation` engine triggering actions based on rules/events.
- `Scheduling` of background tasks, reports, automations.

## Key Features by Category

*(No changes needed in this section)*

## Integration Points

*(Renamed "Key Integration Points" above covers this more comprehensively)*

## Best Practices

### Implementation Guidelines
1.  **Respect Dependencies**: Implement models providing foreign key targets *before* the models that reference them.
2.  **Use Foundational Mixins**: Consistently inherit `Timestamped` and `Auditable` mixins for core models from the start.
3.  Always extend from appropriate base models/mixins like `OrganizationScoped`.
4.  Implement automatic organizational scoping logic early (Phase 1) to ensure core multi-tenancy.
5.  Implement proper validation at the API/Serializer level.
6.  Use organization scoping (`OrganizationScoped` inheritance) where applicable for data segregation.
7.  Implement proper access control using the `Permission` framework.
8.  Implement the historical `Audit` logging system for traceable changes.
9.  Use `Caching` strategically for performance.
10. Implement robust error handling and reporting.
11. Utilize the user-driven `Filtering` framework for flexible API querying.

### Communication Guidelines
*(No changes needed in this section)*

### Security Guidelines
*(No changes needed in this section)*

### Performance Guidelines
*(No changes needed in this section)*

## Future Considerations

*(No changes needed in this section)*

--- END OF UPDATED FILE base_models_classification.md ---