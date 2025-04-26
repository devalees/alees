# Currency API Documentation

## Overview

The Currency API provides access to ISO 4217 currency data. It supports read-only operations for retrieving currency information, including codes, names, symbols, and custom fields.

## Base URL

```
/api/v1/currencies/
```

## Authentication

- **Read operations**: No authentication required
- **Write operations**: Not available (read-only API)

## Endpoints

### List Currencies

Retrieve a list of all active currencies.

```http
GET /api/v1/currencies/
```

#### Query Parameters

| Parameter    | Type    | Description                                    | Default |
|-------------|---------|------------------------------------------------|---------|
| is_active   | boolean | Filter by active status                        | true    |
| search      | string  | Search in code, name fields                    | null    |
| ordering    | string  | Order by field (prefix with - for descending)  | code    |

#### Response

```json
{
    "count": 100,
    "next": "http://api.example.com/api/v1/currencies/?page=2",
    "previous": null,
    "results": [
        {
            "code": "USD",
            "name": "US Dollar",
            "symbol": "$",
            "numeric_code": "840",
            "decimal_places": 2,
            "is_active": true,
            "custom_fields": {}
        },
        {
            "code": "EUR",
            "name": "Euro",
            "symbol": "€",
            "numeric_code": "978",
            "decimal_places": 2,
            "is_active": true,
            "custom_fields": {}
        }
    ]
}
```

### Retrieve Single Currency

Retrieve details for a specific currency by its ISO code.

```http
GET /api/v1/currencies/{code}/
```

#### URL Parameters

| Parameter | Type   | Description           | Example |
|-----------|--------|-----------------------|---------|
| code      | string | ISO 4217 currency code| USD     |

#### Response

```json
{
    "code": "USD",
    "name": "US Dollar",
    "symbol": "$",
    "numeric_code": "840",
    "decimal_places": 2,
    "is_active": true,
    "custom_fields": {}
}
```

## Response Fields

| Field          | Type    | Description                                           |
|----------------|---------|-------------------------------------------------------|
| code           | string  | ISO 4217 3-letter currency code (Primary Key)         |
| name           | string  | Official currency name                                |
| symbol         | string  | Currency symbol (e.g., $, €)                         |
| numeric_code   | string  | ISO 4217 3-digit numeric code                        |
| decimal_places | integer | Number of decimal places commonly used                |
| is_active     | boolean | Whether the currency is currently active              |
| custom_fields  | object  | Additional custom data associated with the currency   |

## Error Responses

### 404 Not Found
Returned when requesting a currency that doesn't exist.

```json
{
    "detail": "Not found."
}
```

### 400 Bad Request
Returned when query parameters are invalid.

```json
{
    "error": "Invalid query parameter value"
}
```

## Examples

### List Active Currencies
```http
GET /api/v1/currencies/
```

### Search Currencies
```http
GET /api/v1/currencies/?search=dollar
```

### Get Specific Currency
```http
GET /api/v1/currencies/USD/
```

### List Inactive Currencies
```http
GET /api/v1/currencies/?is_active=false
```

### Order by Name
```http
GET /api/v1/currencies/?ordering=name
```

## Rate Limiting

The API implements standard rate limiting:
- Unauthenticated: 100 requests per hour
- Authenticated: 1000 requests per hour

## Pagination

Results are paginated with a default page size of 100 items. The response includes:
- `count`: Total number of items
- `next`: URL for the next page (null if no more pages)
- `previous`: URL for the previous page (null if first page)
- `results`: Array of items for the current page

## Notes

1. All currency codes are automatically converted to uppercase.
2. The `custom_fields` object can contain arbitrary JSON data specific to your implementation.
3. The `symbol` field may be empty for some currencies that don't have a widely used symbol.
4. The `numeric_code` field is unique when present but can be null.

## Related Resources

- [ISO 4217 Standard](https://www.iso.org/iso-4217-currency-codes.html)
- [Currency Model Documentation](currency_prd.md) 