# Organization API Documentation

## Overview

The Organization API provides endpoints for managing organizations and their types. Organizations support hierarchical structures, tagging, and various metadata fields.

## Base URLs

```
/api/v1/organizations/      # For Organization endpoints
/api/v1/organization-types/ # For OrganizationType endpoints
```

## Authentication

All endpoints require authentication using JWT tokens.

## Models

### Organization

Represents an organizational unit with hierarchical structure.

#### Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| id | Integer | Unique identifier | No (read-only) |
| name | String | Display name | Yes |
| code | String | Unique identifier code | Yes |
| organization_type | Integer | ID of organization type | Yes |
| status | String | Status (active, inactive, archived) | No |
| parent | Integer | ID of parent organization | No |
| effective_date | Date | Date organization becomes active | No |
| end_date | Date | Date organization ceases to be active | No |
| primary_contact | Integer | ID of primary contact | No |
| primary_address | Integer | ID of primary address | No |
| currency | String | Currency code | No |
| timezone | String | Default timezone | No |
| language | String | Default language | No |
| tags | Array | Tags associated with organization | No |
| metadata | JSON | Additional metadata | No |
| custom_fields | JSON | Custom fields | No |
| created_at | DateTime | Creation timestamp | No (read-only) |
| updated_at | DateTime | Last update timestamp | No (read-only) |

### OrganizationType

Represents different types of organizations.

#### Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| name | String | Unique name | Yes |
| description | Text | Optional description | No |
| created_at | DateTime | Creation timestamp | No (read-only) |
| updated_at | DateTime | Last update timestamp | No (read-only) |
| created_by | Integer | Creator ID | No (read-only) |
| updated_by | Integer | Last updater ID | No (read-only) |

## Endpoints

### Organization Endpoints

#### List Organizations

```
GET /api/v1/organizations/
```

##### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| search | String | Search across name and code |
| organization_type | Integer | Filter by organization type ID |
| status | String | Filter by status |
| parent | Integer | Filter by parent organization ID |
| tags | String | Filter by tag name |
| ordering | String | Order by field (name, code, status, created_at) |

##### Response

```json
{
    "count": 100,
    "next": "http://api.example.com/api/v1/organizations/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Example Corp",
            "code": "EXC",
            "organization_type": 1,
            "status": "active",
            "parent": null,
            "effective_date": "2024-01-01",
            "end_date": null,
            "primary_contact": 1,
            "primary_address": 1,
            "currency": "USD",
            "timezone": "UTC",
            "language": "en",
            "tags": ["customer", "partner"],
            "metadata": {
                "industry": "Technology",
                "size": "Large"
            },
            "custom_fields": {
                "department": "Engineering",
                "region": "North America"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Create Organization

```
POST /api/v1/organizations/
```

##### Request Body

```json
{
    "name": "Example Corp",
    "code": "EXC",
    "organization_type": 1,
    "status": "active",
    "parent": null,
    "effective_date": "2024-01-01",
    "primary_contact": 1,
    "primary_address": 1,
    "currency": "USD",
    "timezone": "UTC",
    "language": "en",
    "tags": ["customer", "partner"],
    "metadata": {
        "industry": "Technology",
        "size": "Large"
    },
    "custom_fields": {
        "department": "Engineering",
        "region": "North America"
    }
}
```

#### Retrieve Organization

```
GET /api/v1/organizations/{id}/
```

#### Update Organization

```
PUT /api/v1/organizations/{id}/
PATCH /api/v1/organizations/{id}/
```

#### Delete Organization

```
DELETE /api/v1/organizations/{id}/
```

#### Get Descendants

```
GET /api/v1/organizations/{id}/descendants/
```

Returns all descendant organizations in the hierarchy.

#### Get Ancestors

```
GET /api/v1/organizations/{id}/ancestors/
```

Returns all ancestor organizations in the hierarchy.

### OrganizationType Endpoints

#### List Organization Types

```
GET /api/v1/organization-types/
```

##### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| search | String | Search across name and description |
| name | String | Filter by exact name |
| ordering | String | Order by field (name) |

##### Response

```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "name": "Customer",
            "description": "Customer organizations",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "created_by": 1,
            "updated_by": 1
        }
    ]
}
```

#### Retrieve Organization Type

```
GET /api/v1/organization-types/{name}/
```

## Validation Rules

### Organization

1. **Code Validation**:
   - Must be unique
   - Cannot be changed if already set

2. **Custom Fields**:
   - Must be a valid JSON object
   - Can be null

3. **Metadata**:
   - Must be a valid JSON object
   - Can be null

4. **Relationships**:
   - `organization_type` must exist
   - `primary_contact` must exist if provided
   - `primary_address` must exist if provided
   - `currency` must exist if provided
   - `parent` must exist if provided

### OrganizationType

1. **Name**:
   - Must be unique
   - Cannot be changed after creation

## Error Responses

### 400 Bad Request

```json
{
    "code": ["An organization with code 'EXC' already exists."]
}
```

### 401 Unauthorized

```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden

```json
{
    "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found

```json
{
    "detail": "Not found."
}
```

## Examples

### Creating a New Organization

```json
{
    "name": "Tech Solutions Inc",
    "code": "TSI",
    "organization_type": 1,
    "status": "active",
    "parent": null,
    "effective_date": "2024-01-01",
    "primary_contact": 1,
    "primary_address": 1,
    "currency": "USD",
    "timezone": "America/New_York",
    "language": "en",
    "tags": ["technology", "partner"],
    "metadata": {
        "industry": "Software",
        "size": "Medium"
    },
    "custom_fields": {
        "specialization": "Cloud Computing",
        "region": "North America"
    }
}
```

### Updating Organization Status

```json
{
    "status": "inactive"
}
```

### Adding Tags to Organization

```json
{
    "tags": ["technology", "partner", "premium"]
}
```

### Setting Parent Organization

```json
{
    "parent": 2
}
```

### Creating Organization Hierarchy

```json
// Parent Organization
{
    "name": "Global Corp",
    "code": "GLC",
    "organization_type": 1,
    "status": "active"
}

// Child Organization
{
    "name": "North America Division",
    "code": "NAD",
    "organization_type": 1,
    "status": "active",
    "parent": 1  // ID of Global Corp
}
``` 