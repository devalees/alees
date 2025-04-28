Okay, thank you for the update! Acknowledged that `OrganizationType` is also complete.

That simplifies Phase 1 slightly. Here is the updated refined implementation ranking, reflecting that `Timestamped`, `Auditable`, `Currency`, `Address`, and `OrganizationType` are finished:

---

*(Completed: `Timestamped`, `Auditable`, `Currency`, `Address`, `OrganizationType`)*

**Phase 1: Core Foundational Entities, Tracking & Scoping (Continued)**

1.  **`UserProfile.md`** (Extends User, depends TS/A)
2.  **`Contact.md`** (Depends TS/A, Org[nullable FK])
4.  **`Organization.md`** (Depends TS/A, OrgType, Contact[nullable FK], Address[nullable FK], Currency[nullable FK], MPTT, Taggit)
5.  **`OrganizationMembership.md`** (Depends User, Org, Group, TS/A)
6.  **`OrganizationScoped.md` (Mixin Definition Only)** (Depends Org)
7.  **`FileStorage.md`** (Depends TS/A/OS, User, Org, Taggit)

**Phase 1.5: RBAC & Scoping Enforcement**

8.  **`rbac_strategy_org_aware.md`** (Strategy Doc)
9.  **Implement Org-Aware `has_perm`** (Logic Implementation)
10. **`OrganizationScoped.md` (Enforcement Logic Implementation)** (Depends Mixin def, OrgMembership, RBAC logic)

**Phase 2: System Infrastructure & Other Base Data**

11. **`Status.md`** (Depends TS/A)
12. **`AuditLogging.md`** (Depends TS, User, Org, ContentType, Signals)
13. **`UoM.md`** (Depends TS/A)
14. **`Category.md`** (Depends TS/A, MPTT)
15. **`Tagging.md`** (Integrates Taggit library)

**Phase 3: Core Business Logic - Products & Inventory**

16. **`Tax.md`** (Depends TS/A, MPTT maybe)
17. **`Product.md`** (Depends TS/A/OS, Category, UoM, Status)
18. **`Warehouse.md`** (Depends TS/A/OS, Address)
19. **`StockLocation.md`** (Depends TS/A/OS, Warehouse, MPTT)

**Phase 4: Apply Tagging & Add Document Handling / Workflows / Filtering**

20. **Apply `TaggableManager`** to relevant models implemented so far (Org, Contact, Product, Warehouse, FileStorage) via migrations.
21. **`DocumentSystem.md`** (Depends TS/A/OS, FileStorage, Category, Status)
22. **Apply `TaggableManager`** to `Document`.
23. **`Workflow.md`** (Integrates FSM, depends Status, AuditLog, RBAC)
24. **`advanced_filtering_prd.md`** (Framework)

**Phase 5: Communication & Collaboration**

25. **`Notification.md`** (Depends TS/A/OS, User, UserProfile, Org, Celery)
26. **`Comment.md`** (Depends TS/A/OS, User, FileStorage, ContentType)
27. **`Chat.md`** (Depends TS/A/OS, User, Org, FileStorage, Channels)
28. **`VideoMeeting.md`** (Depends TS/A/OS, User, Org, ContentType, Ext API)

**Phase 6: Advanced Features & Automation**

29. **`Search.md`** (Integrates ES, depends Models, Signals, Celery[opt])
30. **`ExportImport.md`** (Depends TS/A/OS, User, Org, FileStorage, ContentType, Celery, Libs)
31. **`Automation.md`** (Depends TS/A/OS, User, Org, ContentType, Celery, Cron)

---

This updated ranking looks correct based on the completed items and dependencies.

The next item on the list is **`UserProfile.md`**. Please provide the PRD and Implementation Steps for `UserProfile` when you're ready!