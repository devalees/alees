Okay, I understand. You want to enhance the ranked list by adding explicit relationship details under each model/system to make the dependencies even clearer. This is a good idea for visualizing the connections directly within the implementation plan.

I will add a `Relationships:` section under each item, listing the primary models it **connects TO** (via ForeignKey, OneToOne, M2M) and the models that **connect TO IT** (its dependents).

--- START OF FILE base_models_ranking_with_relations.md ---

# Implementation Plan: Models & Systems Ranked by Dependency

## Overview

This document outlines the prioritized implementation order for the core models, systems, and integration strategies of the ERP backend. The ranking is based on logical dependencies, ensuring foundational components are built before features relying on them. The goal is to guide the generation of detailed, step-by-step implementation documents following a TDD approach. Relationship details are included for clarity.

## Implementation Phases & Order

*(Implementation steps documents will be generated based on these PRDs/Strategies in this order.)*

**Phase 1: Core Foundational Entities, Tracking & Scoping**
*Goal: Establish minimal independent entities, user identity, base data types, essential tracking fields (mixins), the Organization model, basic permissions, and the foundational multi-tenancy scoping mechanism.*

1.  **`Timestamped.md`** (Abstract Base Model PRD)
    *   *Relationships:* None (Abstract - provides fields via inheritance).
2.  **`Auditable.md`** (Abstract Base Model PRD)
    *   *Relationships:*
        *   Connects TO: `User` (via `created_by`, `updated_by` ForeignKeys, SET_NULL).
        *   Provides fields via inheritance.
3.  **`UserProfile.md`** (PRD for model extending Django User)
    *   *Relationships:*
        *   Connects TO: `User` (via `user` OneToOneField, CASCADE), `User` (via `manager` ForeignKey, SET_NULL, nullable), `FileStorage` (via `profile_picture` ForeignKey, SET_NULL, nullable - *Deferred if FileStorage later*).
        *   Inherits FROM: `Timestamped`, `Auditable`.
4.  **`Currency.md`** (Model PRD)
    *   *Relationships:*
        *   Inherits FROM: `Timestamped`, `Auditable`.
        *   Connected TO BY: `Organization` (nullable FK), `ProductPrice` (later), `Invoice` (later), etc.
5.  **`Address.md`** (Model PRD)
    *   *Relationships:*
        *   Inherits FROM: `Timestamped`, `Auditable`.
        *   Connected TO BY: `Organization` (nullable FK), `ContactAddress` (CASCADE FK), `Warehouse` (nullable FK).
6.  **`OrganizationType.md`** (Model PRD)
    *   *Relationships:*
        *   Inherits FROM: `Timestamped`, `Auditable`.
        *   Connected TO BY: `Organization` (PROTECT FK).
7.  **`Organization.md`** (Model PRD)
    *   *Relationships:*
        *   Connects TO: `OrganizationType` (PROTECT FK), `Organization` (via `parent` TreeForeignKey, PROTECT, nullable), `Contact` (via `primary_contact` FK, SET_NULL, nullable), `Address` (via `primary_address` FK, SET_NULL, nullable), `Currency` (via `currency` FK, PROTECT, nullable).
        *   Inherits FROM: `Timestamped`, `Auditable`. Uses MPTT. Uses Taggit.
        *   Connected TO BY: `OrganizationMembership` (CASCADE FK), `OrganizationScoped` (PROTECT FK - implemented via inheriting models), `Contact` (nullable FK), `AuditLog` (nullable FK).
8.  **`Contact.md`** (Model PRD)
    *   *Relationships:*
        *   Connects TO: `Organization` (via `linked_organization` FK, SET_NULL, nullable).
        *   Inherits FROM: `Timestamped`, `Auditable`. Uses Taggit.
        *   Connected TO BY: `Organization` (nullable FK), `ContactEmailAddress` (CASCADE FK), `ContactPhoneNumber` (CASCADE FK), `ContactAddress` (CASCADE FK).
9.  **`ContactEmailAddress.md` / `ContactPhoneNumber.md` / `ContactAddress.md`** (Defined within `Contact.md` scope)
    *   *Relationships:*
        *   Connect TO: `Contact` (CASCADE FK). `ContactAddress` also connects to `Address` (CASCADE FK).
        *   Inherit FROM: `Timestamped`, `Auditable`.
10. **`OrganizationMembership.md`** (Model PRD)
    *   *Relationships:*
        *   Connects TO: `User` (CASCADE FK), `Organization` (CASCADE FK), `Group` (Role) (PROTECT FK).
        *   Inherits FROM: `Timestamped`, `Auditable`.
        *   Connected TO BY: Queried by `User.get_organizations()` and Org-Aware RBAC logic.
11. **`OrganizationScoped.md` (Mixin Definition Only)**
    *   *Relationships:*
        *   Connects TO: `Organization` (via `organization` ForeignKey, PROTECT).
        *   Abstract - provides field via inheritance.
12. **`FileStorage.md`** (PRD for file metadata model)
    *   *Relationships:*
        *   Connects TO: `User` (via `uploaded_by` FK, SET_NULL, nullable), `Organization` (via `OrganizationScoped`).
        *   Inherits FROM: `Timestamped`, `Auditable`, `OrganizationScoped`. Uses Taggit.
        *   Connected TO BY: `Document` (PROTECT FK), `Comment` (M2M), `ChatMessage` (M2M), `UserProfile` (nullable FK), etc.
13. **`OrganizationScoped.md` (Enforcement Logic Implementation)**
    *   *Relationships:* Conceptual link - This ViewSet Mixin *uses* the `OrganizationScoped` model definition, the `User.get_organizations()` method (derived from `OrganizationMembership`), and applies filtering to QuerySets of inheriting models.

**Phase 2: System Infrastructure & Other Base Data**
*Goal: Implement further core system functionalities (logging, status definitions) and remaining fundamental business data types.*
14. `Status.md` (Model PRD)
    *   *Relationships:* Inherits `Timestamped`, `Auditable`. Referenced by `status` CharFields in other models (e.g., `Product`, `Document`, `Order`).
15. `AuditLogging.md` (`AuditLog` model + mechanism PRD)
    *   *Relationships:* Connects TO: `User` (nullable FK), `Organization` (nullable FK), `ContentType` (nullable FK). Uses GFK (`content_object`). Inherits `Timestamped`. Triggered via signals from many other models.
16. `UoM.md` (Unit of Measure Model PRD)
    *   *Relationships:* Inherits `Timestamped`, `Auditable`. Connected TO BY: `Product` (PROTECT FK).
17. `Category.md` (Model PRD)
    *   *Relationships:* Connects TO: `Category` (via `parent` TreeForeignKey, CASCADE/PROTECT). Inherits `Timestamped`, `Auditable`. Uses MPTT. Connected TO BY: `Product` (PROTECT FK/M2M), `Document` (PROTECT FK).
18. `Tagging.md` (Integration strategy PRD)
    *   *Relationships:* Integrates `django-taggit`. Adds `TaggableManager` (conceptual M2M via `TaggedItem`) to models like `Organization`, `Contact`, `Product`, `Document`, `FileStorage`.
19. `rbac_strategy_org_aware.md` (NEW Strategy Doc)
    *   *Relationships:* Defines strategy using `User`, `Group`, `Permission`, `OrganizationMembership`. Provides logic for checking permissions.
20. Implement Org-Aware `has_perm` (Requires Steps Document)
    *   *Relationships:* Implements logic querying `User`, `Group`, `Permission`, `OrganizationMembership`.

**Phase 3: Core Business Logic - Products & Inventory**
*Goal: Implement the central product catalog and foundational inventory/tax definitions.*
21. `Tax.md` (PRD for `TaxJurisdiction`, `TaxCategory`, `TaxRate` models)
    *   *Relationships:* `TaxRate` connects to `TaxJurisdiction` (CASCADE) and `TaxCategory` (CASCADE, nullable). `TaxJurisdiction` potentially uses MPTT (connects to self). All inherit `Timestamped`, `Auditable`. `TaxCategory` referenced by `Product` (PROTECT FK).
22. `Product.md` (Model PRD)
    *   *Relationships:* Connects TO: `Category` (PROTECT FK, nullable), `UnitOfMeasure` (PROTECT FK). Inherits `Timestamped`, `Auditable`, `OrganizationScoped`. Uses Taggit. Connected TO BY: `StockLevel` (later), `OrderLine` (later), etc. References `Status`.
23. `Warehouse.md` (Model PRD)
    *   *Relationships:* Connects TO: `Address` (PROTECT FK, nullable). Inherits `Timestamped`, `Auditable`, `OrganizationScoped`. Uses Taggit. Connected TO BY: `StockLocation` (CASCADE FK).
24. `StockLocation.md` (*PRD Needed*)
    *   *Relationships:* Connects TO: `Warehouse` (CASCADE FK), `StockLocation` (via `parent` TreeForeignKey, CASCADE). Inherits `Timestamped`, `Auditable`, `OrganizationScoped`. Uses MPTT. Connected TO BY: `StockLevel` (later).

**Phase 4: Data Handling & Enhanced Infrastructure**
*Goal: Add capabilities for documents, advanced filtering, and workflows.*
25. `DocumentSystem.md` (`Document` model PRD)
    *   *Relationships:* Connects TO: `FileStorage` (PROTECT FK), `Category` ( PROTECT FK, nullable), `ContentType` (CASCADE FK). Uses GFK. Inherits `Timestamped`, `Auditable`, `OrganizationScoped`. Uses Taggit. References `Status`.
26. `Workflow.md` (Integration strategy PRD)
    *   *Relationships:* Integrates library (e.g., `django-fsm`). Operates on models with `status` fields (e.g., `Product`, `Document`, `Order`). Triggers `AuditLogging` via signals. Uses `RBAC` for transition permissions.
27. `advanced_filtering_prd.md` (Filtering System PRD)
    *   *Relationships:* Defines custom `FilterBackend`. Operates on QuerySets of various models. May optionally define `StoredFilter` model linking to `User`, `Organization`, `ContentType`.

**Phase 5: Communication & Collaboration**
*Goal: Implement features for user interaction and communication.*
28. `Notification.md` (Notification System PRD)
    *   *Relationships:* `Notification` model connects to `User` (CASCADE FK), `Organization` (SET_NULL FK), `ContentType` (SET_NULL FK). Uses GFK. Inherits `Timestamped`, `Auditable`, `OrganizationScoped`. `NotificationTemplate` model inherits `Timestamped`, `Auditable`. Relies on Celery.
29. `Comment.md` (Comment Model PRD)
    *   *Relationships:* Connects TO: `User` (SET_NULL FK for author), `ContentType` (CASCADE FK), `Comment` (via `parent` FK, CASCADE), `FileStorage` (M2M). Uses GFK. Inherits `Timestamped`, `Auditable`, `OrganizationScoped`.
30. `Chat.md` (Chat System PRD)
    *   *Relationships:* `ChatRoom` links M2M to `User`. `ChatMessage` links FK to `ChatRoom` (CASCADE), `User` (SET_NULL), `ChatMessage` (`parent` FK, SET_NULL), M2M to `FileStorage`. Both inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Relies on Channels infrastructure.
31. `VideoMeeting.md` (Integration strategy + ERP models PRD)
    *   *Relationships:* `Meeting` links FK to `User` (host), `ContentType` (nullable). `MeetingParticipant` links FK to `Meeting` (CASCADE), `User` (CASCADE). Both inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Relies on external provider API, Celery (optional), `FileStorage` (optional).

**Phase 6: Advanced Features & Automation**
*Goal: Implement search, data import/export, and the automation engine.*
32. `Search.md` (Search System Integration PRD)
    *   *Relationships:* Integrates external Search Engine (Elasticsearch/OpenSearch). Indexing pipeline uses signals from various models (`Product`, `Organization`, etc.). API post-filters results based on RBAC/Org Scoping. Relies on Celery (optional).
33. `ExportImport.md` (Framework PRD + `DataJob` model)
    *   *Relationships:* `DataJob` model connects to `User`, `Organization`, `ContentType` (nullable), `FileStorage` (nullable FKs). Framework uses `django-import-export` resources defined per target model. Relies on Celery, Advanced Filtering parser.
34. `Automation.md` (Automation Rule Engine PRD)
    *   *Relationships:* `AutomationRule` connects to `ContentType`. `RuleCondition` connects to `AutomationRule`. `RuleAction` connects to `AutomationRule`. `AutomationLog` connects to `AutomationRule`, `User`, `Organization`, `ContentType` and uses GFK. All inherit base mixins (`TS`, `A`, `OS`). Relies on Celery (Workers+Beat), Signals, Condition/Action logic interacting with various models/services.

**Phase 7: Analytics & Reporting (Future Phase)**
*Goal: Implement data analysis and reporting capabilities.*
35. *(Analytics Implementation)*
36. *(Reporting Implementation)*

## Notes on Dependencies and Phasing
*(Same as previous version)*

--- END OF FILE base_models_ranking_with_relations.md ---

This version explicitly adds the primary relationships under each item in the ranked list. Let me know if this added detail is helpful!