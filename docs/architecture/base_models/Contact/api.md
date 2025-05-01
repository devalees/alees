# Contact API Documentation

## Overview

The Contact API provides endpoints for managing contact information, including personal details, communication channels (email, phone, address), and organization relationships.

## Base URL

```
/api/v1/contacts/
```

## Authentication

All endpoints require authentication using JWT tokens.

## Models

### Contact

Represents a person or entity with contact information.

#### Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| id | Integer | Unique identifier | No (read-only) |
| first_name | String | First name | Yes |
| last_name | String | Last name | Yes |
| title | String | Professional title | No |
| organization_name | String | Name of organization (if not linked) | No |
| linked_organization | Integer | ID of linked Organization | No |
| linked_organization_name | String | Name of linked organization | No (read-only) |
| contact_type | String | Type of contact (primary, billing, support, technical, other) | No |
| status | String | Contact status (active, inactive) | No |
| source | String | How contact was acquired (website, referral, conference, other) | No |
| notes | Text | Additional notes | No |
| tags | Array | Tags associated with contact | No |
| custom_fields | JSON | Additional custom fields | No |
| email_addresses | Array | Email addresses | No |
| phone_numbers | Array | Phone numbers | No |
| addresses | Array | Physical addresses | No |
| created_at | DateTime | Creation timestamp | No (read-only) |
| updated_at | DateTime | Last update timestamp | No (read-only) |

### Organization Linking

Contacts can be associated with organizations in two ways:

1. **Linked Organization** (`linked_organization`):
   - References an existing Organization in the system
   - Provides full relationship capabilities
   - Cannot be used with `organization_name`

2. **Organization Name** (`organization_name`):
   - Simple text field for organization name
   - Used when organization doesn't exist in system
   - Cannot be used with `linked_organization`

## Endpoints

### List Contacts

```
GET /api/v1/contacts/
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| search | String | Search across first_name, last_name, organization_name, title |
| first_name | String | Filter by first name |
| last_name | String | Filter by last name |
| contact_type | String | Filter by contact type |
| status | String | Filter by status |
| source | String | Filter by source |
| has_organization | Boolean | Filter contacts with/without linked organization |

#### Response

```json
{
    "count": 100,
    "next": "http://api.example.com/api/v1/contacts/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "title": "Manager",
            "organization_name": null,
            "linked_organization": 1,
            "linked_organization_name": "Example Corp",
            "contact_type": "primary",
            "status": "active",
            "source": "website",
            "email_addresses": [...],
            "phone_numbers": [...],
            "addresses": [...],
            "tags": ["customer", "vip"],
            "custom_fields": {},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

### Create Contact

```
POST /api/v1/contacts/
```

#### Request Body

```json
{
    "first_name": "John",
    "last_name": "Doe",
    "title": "Manager",
    "organization_name": "Example Corp",  // OR
    "linked_organization": 1,             // Cannot use both
    "contact_type": "primary",
    "status": "active",
    "source": "website",
    "email_addresses": [
        {
            "email": "john@example.com",
            "email_type": "work",
            "is_primary": true
        }
    ],
    "phone_numbers": [
        {
            "phone_number": "+1234567890",
            "phone_type": "mobile",
            "is_primary": true
        }
    ],
    "addresses": [
        {
            "address": {
                "street_address_1": "123 Main St",
                "city": "New York",
                "state_province": "NY",
                "postal_code": "10001",
                "country": {"code": "US", "name": "United States"}
            },
            "address_type": "work",
            "is_primary": true
        }
    ],
    "tags": ["customer", "vip"],
    "custom_fields": {
        "department": "Engineering",
        "position": "Senior Developer"
    }
}
```

### Retrieve Contact

```
GET /api/v1/contacts/{id}/
```

### Update Contact

```
PUT /api/v1/contacts/{id}/
PATCH /api/v1/contacts/{id}/
```

### Delete Contact

```
DELETE /api/v1/contacts/{id}/
```

## Validation Rules

1. **Organization Fields**:
   - Cannot provide both `organization_name` and `linked_organization`
   - `linked_organization` must reference an existing Organization
   - `organization_name` must be a string if provided

2. **Required Fields**:
   - `first_name` and `last_name` are required for new contacts
   - At least one name field must be provided

3. **Communication Channels**:
   - Email addresses must be valid format
   - Phone numbers must be in E.164 format
   - Only one primary email/phone/address per contact

4. **Custom Fields**:
   - Must be a valid JSON object
   - No specific field validation (application-specific)

## Error Responses

### 400 Bad Request

```json
{
    "organization_name": ["Cannot provide both organization name and organization ID"]
}
```

### 401 Unauthorized

```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found

```json
{
    "detail": "Not found."
}
```

## Examples

### Creating a Contact with Linked Organization

```json
{
    "first_name": "Jane",
    "last_name": "Smith",
    "linked_organization": 1,
    "email_addresses": [
        {
            "email": "jane@example.com",
            "email_type": "work",
            "is_primary": true
        }
    ]
}
```

### Creating a Contact with Organization Name

```json
{
    "first_name": "Bob",
    "last_name": "Johnson",
    "organization_name": "External Company Inc",
    "email_addresses": [
        {
            "email": "bob@external.com",
            "email_type": "work",
            "is_primary": true
        }
    ]
}
```

### Updating Organization Link

```json
{
    "linked_organization": 2  // Change to different organization
}
```

### Removing Organization Link

```json
{
    "linked_organization": null  // Remove organization link
}
``` 