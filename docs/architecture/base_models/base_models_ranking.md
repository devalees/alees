Okay, here is the full, updated `base_models_ranking.md` file incorporating the cleaner naming convention, the explicit inclusion of the Search PRD (`Search.md`), and the categorization into Phases based on our refined dependency analysis.

--- START OF FILE base_models_ranking.md ---

# Implementation Plan: Models & Systems Ranked by Dependency

## Overview

This document outlines the prioritized implementation order for the core models, systems, and integration strategies of the ERP backend. The ranking is based on logical dependencies identified through PRD reviews, ensuring foundational components are built before features relying on them. The goal is to guide the generation of detailed, step-by-step implementation documents following a TDD approach.

## Implementation Phases & Order

*(PRDs listed here represent the documents defining the requirements/strategy for each component. Implementation steps documents will be generated based on these in this order.)*

**Phase 1: Core Foundational Entities, Tracking & Scoping**
*Goal: Establish minimal independent entities, user identity, base data types, essential tracking fields (mixins), the Organization model, basic permissions, and the foundational multi-tenancy scoping mechanism.*
1.  `Timestamped.md` (Abstract Base Model PRD)
2.  `UserProfile.md` (PRD for model extending Django User)
3.  `Auditable.md` (Abstract Base Model PRD)
4.  `Currency.md` (Model PRD)
5.  `Address.md` (Model PRD)
6.  `OrganizationType.md` (Model PRD)
7.  `Organization.md` (Model PRD)
8.  `Contact.md` (Model PRD - includes related communication channel models)
9.  `RBAC.md` (PRD for extending Django Auth + FieldPermission model)
10. `OrganizationScoped.md` (PRD for Abstract Base Model / Mechanism - includes Mixin definition + Enforcement Logic implementation)

**Phase 2: System Infrastructure & Other Base Data**
*Goal: Implement further core system functionalities (logging, status definitions) and remaining fundamental business data types.*
11. `Status.md` (Model PRD)
12. `AuditLogging.md` (PRD for `AuditLog` model + capturing mechanism)
13. `UoM.md` (Unit of Measure Model PRD)
14. `Category.md` (PRD for Generic, Hierarchical Category Model)
15. `Tagging.md` (PRD for Integration strategy using `django-taggit`)

**Phase 3: Core Business Logic - Products & Inventory**
*Goal: Implement the central product catalog and foundational inventory/tax definitions.*
16. `Tax.md` (PRD for `TaxJurisdiction`, `TaxCategory`, `TaxRate` models)
17. `Product.md` (Model PRD)
18. `Warehouse.md` (Model PRD)
19. `StockLocation.md` (Model PRD)

**Phase 4: Data Handling & Enhanced Infrastructure**
*Goal: Add capabilities for managing files, documents, advanced filtering, and workflows.*
20. `FileStorage.md` (PRD for file metadata model)
21. `DocumentSystem.md` (PRD for `Document` model linking to FileStorage)
22. `Workflow.md` (PRD for Workflow/State Machine Integration strategy)
23. `Filtering.md` (PRD for Advanced Filtering System)

**Phase 5: Communication & Collaboration**
*Goal: Implement features for user interaction and communication.*
24. `Notification.md` (PRD for Notification System - `Notification`, `NotificationTemplate` models + async delivery)
25. `Comment.md` (PRD for Comment Model - Generic Relations, Threading, Attachments)
26. `Chat.md` (PRD for Chat System - `ChatRoom`, `ChatMessage` models + Channels integration)
27. `VideoMeeting.md` (PRD for Video Meeting Integration strategy + ERP models)

**Phase 6: Advanced Features & Automation**
*Goal: Implement search, data import/export, and the automation engine.*
28. `Search.md` (PRD for Search System Integration)
29. `ExportImport.md` (PRD for Export/Import Framework + `DataJob` model)
30. `Automation.md` (PRD for Automation Rule Engine - Models + Celery/Signal integration)

**Phase 7: Analytics & Reporting (Future Phase)**
*Goal: Implement data analysis and reporting capabilities (strategy TBD - native or BI tool integration).*
31. *(Analytics Implementation - Based on chosen Analytics/Reporting Strategy)*
32. *(Reporting Implementation - Based on chosen Analytics/Reporting Strategy)*

## Notes on Dependencies and Phasing

*   **Phase 1 is critical:** Establishes the absolute core entities and mechanisms (User, Org, Scoping, basic tracking) needed by almost everything else.
*   **Infrastructure Setup:** Core infrastructure (Postgres, Redis, Celery setup, File Storage strategy) must be configured alongside or just before Phase 1, guided by their respective strategy/setup documents. Testing infrastructure setup is also needed early.
*   **Strategies Inform Implementation:** High-level strategy documents (API, Logging, Testing, Security, Config, etc.) guide the *how* during the implementation of models/features in each phase.
*   **Library Integration:** Phases involving libraries (`django-mptt`, `django-taggit`, `django-import-export`, `django-parler`, workflow library, Channels, `django-redis`, etc.) require installing and configuring those libraries at the start of that phase.
*   **Flexibility:** While dependencies dictate the early phases strongly, the order of implementation for later phases (e.g., Phase 4 onwards) can often be adjusted based on business priorities, provided the core dependencies are met. For instance, Notifications might be implemented earlier if needed by core workflows.

This document provides the roadmap for generating the detailed implementation steps checklists for each component in a logical, dependency-aware sequence.

--- END OF FILE base_models_ranking.md ---