# Organization Type API Documentation

## Overview

The Organization Type API provides endpoints for managing different types of organizations in the Alees ERP system. This API allows you to retrieve, filter, and order organization types such as Company, Department, Customer, etc.

### Base URL

```
{{base_url}}/api/v1/organization/organization-types/
```

### Authentication

- **Read-only Access**: No authentication required
- **Write Access**: Requires authentication (not implemented in current version)

### Response Format

All responses are in JSON format with the following structure:

```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "name": "Company",
            "description": "Primary legal entity or top-level organization."
        }
    ]
}
```

## Endpoints

### List Organization Types

Retrieves a list of all organization types with optional filtering, ordering, and pagination.

**URL:** `GET /api/v1/organization/organization-types/`

**Query Parameters:**
- `name` (optional): Filter by organization type name
- `ordering` (optional): Order results by field (e.g., `name`, `-name` for descending)
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of results per page

**Response:**
- Status Code: 200 OK
- Content-Type: application/json

**Example Request:**
```http
GET /api/v1/organization/organization-types/
Accept: application/json
```

**Example Response:**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "name": "Company",
            "description": "Primary legal entity or top-level organization."
        },
        {
            "name": "Department",
            "description": "A functional department within a division or company."
        }
    ]
}
```

### Retrieve Organization Type

Retrieves details of a specific organization type by its name.

**URL:** `GET /api/v1/organization/organization-types/{name}/`

**Path Parameters:**
- `name`: The name of the organization type to retrieve

**Response:**
- Status Code: 200 OK
- Content-Type: application/json

**Example Request:**
```http
GET /api/v1/organization/organization-types/Company/
Accept: application/json
```

**Example Response:**
```json
{
    "name": "Company",
    "description": "Primary legal entity or top-level organization."
}
```

### Filter Organization Types

Filters organization types by name.

**URL:** `GET /api/v1/organization/organization-types/?name={filter_name}`

**Query Parameters:**
- `name`: The name to filter by

**Response:**
- Status Code: 200 OK
- Content-Type: application/json

**Example Request:**
```http
GET /api/v1/organization/organization-types/?name=Company
Accept: application/json
```

**Example Response:**
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "name": "Company",
            "description": "Primary legal entity or top-level organization."
        }
    ]
}
```

### Order Organization Types

Orders organization types by name (ascending or descending).

**URL:** `GET /api/v1/organization/organization-types/?ordering={order_by}`

**Query Parameters:**
- `ordering`: Field to order by (e.g., `name`, `-name` for descending)

**Response:**
- Status Code: 200 OK
- Content-Type: application/json

**Example Request:**
```http
GET /api/v1/organization/organization-types/?ordering=-name
Accept: application/json
```

**Example Response:**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "name": "Department",
            "description": "A functional department within a division or company."
        },
        {
            "name": "Company",
            "description": "Primary legal entity or top-level organization."
        }
    ]
}
```

## Error Responses

### 404 Not Found

Returned when the requested organization type does not exist.

**Example Response:**
```json
{
    "detail": "Not found."
}
```

### 400 Bad Request

Returned when invalid query parameters are provided.

**Example Response:**
```json
{
    "detail": "Invalid ordering parameter."
}
```

## Notes

- All endpoints are read-only in the current implementation
- The API supports pagination, filtering, and ordering
- Organization type names are unique and case-sensitive
- The API uses Django REST Framework's built-in pagination, filtering, and ordering features

## Postman Collection

A Postman collection is available for testing these endpoints:
- Collection: `organizationtype_postman_collection.json`
- Environment: `organizationtype_postman_environment.json`

These files can be imported into Postman for easy testing of the API endpoints. 