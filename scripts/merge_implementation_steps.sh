#!/bin/bash

# Create base file with header
echo "# Base Models Implementation Steps" > docs/architecture/merged_base_models_implementation_steps.md
echo "" >> docs/architecture/merged_base_models_implementation_steps.md
echo "## Table of Contents" >> docs/architecture/merged_base_models_implementation_steps.md
echo "" >> docs/architecture/merged_base_models_implementation_steps.md

# Add table of contents
cat << 'EOF' >> docs/architecture/merged_base_models_implementation_steps.md
1. [Core Models](#core-models)
   - [Organization](#organization)
   - [Organization Type](#organization-type)
   - [User Profile](#user-profile)
   - [Contact](#contact)
   - [Address](#address)

2. [System Models](#system-models)
   - [Audit Logging](#audit-logging)
   - [Auditable](#auditable)
   - [Timestamped](#timestamped)
   - [Status](#status)

3. [Authentication & Authorization](#authentication--authorization)
   - [Auth API](#auth-api)
   - [Organization Membership](#organization-membership)
   - [Organization Scoped](#organization-scoped)

4. [Business Models](#business-models)
   - [Product](#product)
   - [Category](#category)
   - [Tax](#tax)
   - [Currency](#currency)
   - [Unit of Measure](#unit-of-measure)
   - [Warehouse](#warehouse)
   - [Stock Location](#stock-location)

5. [Communication & Collaboration](#communication--collaboration)
   - [Chat](#chat)
   - [Comment](#comment)
   - [Notification](#notification)
   - [Video Meeting](#video-meeting)

6. [Document Management](#document-management)
   - [Document System](#document-system)
   - [File Storage](#file-storage)
   - [Export/Import](#exportimport)

7. [System Features](#system-features)
   - [Search](#search)
   - [Filtering](#filtering)
   - [Tagging](#tagging)
   - [Workflow](#workflow)
   - [Automation](#automation)

---
EOF

# Core Models
echo -e "\n## Core Models\n" >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Organization\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Organization/organization_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Organization Type\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/OrganizationType/organizationtype_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### User Profile\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/UserProfile/userprofile_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Contact\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Contact/contact_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Address\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Address/address_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md

# System Models
echo -e "\n## System Models\n" >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Audit Logging\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/AuditLogging/auditlogging_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Auditable\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Auditable/auditable_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Timestamped\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Timestamped/timestamped_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Status\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Status/status_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md

# Authentication & Authorization
echo -e "\n## Authentication & Authorization\n" >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Auth API\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Auth/auth_api_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Organization Membership\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/OrganizationMembership/organizationmembership_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Organization Scoped\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/OrganizationScoped/organizationscoped_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md

# Business Models
echo -e "\n## Business Models\n" >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Product\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Product/product_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Category\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Category/category_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Tax\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Tax/tax_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Currency\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Currency/currency_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Unit of Measure\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/UoM/uom_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Warehouse\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Warehouse/warehouse_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Stock Location\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/StockLocation/stocklocation_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md

# Communication & Collaboration
echo -e "\n## Communication & Collaboration\n" >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Chat\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Chat/chat_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Comment\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Comment/comment_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Notification\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Notification/notification_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Video Meeting\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/VideoMeeting/videomeeting_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md

# Document Management
echo -e "\n## Document Management\n" >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Document System\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/DocumentSystem/document_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### File Storage\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/FileStorage/filestorage_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Export/Import\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/ExportImport/exportimport_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md

# System Features
echo -e "\n## System Features\n" >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Search\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Search/search_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Filtering\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Filtering/filtering_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Tagging\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Tagging/tagging_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Workflow\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Workflow/workflow_integration_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md
echo -e "\n### Automation\n" >> docs/architecture/merged_base_models_implementation_steps.md
cat docs/architecture/base_models/Automation/automation_implementation_steps.md >> docs/architecture/merged_base_models_implementation_steps.md 