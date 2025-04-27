# Address Model Documentation

## Quick Start
The Address model provides a flexible and robust way to store physical addresses in the ERP system. It is designed to be used as a nested resource within other entities like Organizations, UserProfiles, etc.

## Key Features
- Full postal address support (street, city, state, postal code, country)
- Geolocation support (latitude/longitude)
- Custom fields with validation
- Audit trail
- Status tracking
- Country validation via django-countries

## Implementation Approach
Addresses are implemented as nested resources rather than standalone endpoints. This means:
- No direct API endpoints for addresses
- Addresses are created/updated through their parent entities
- Strong validation ensures data integrity
- Flexible custom fields support specific use cases

## Documentation Index
1. [Implementation Steps](address_implementation_steps.md) - Step-by-step guide to implementation
2. [Architectural Decisions](address_architectural_decisions.md) - Key design decisions and rationale
3. [PRD](address_prd.md) - Product Requirements Document

## Usage Example
```python
# In a parent model (e.g., Organization)
class Organization(models.Model):
    name = models.CharField(max_length=255)
    address = models.ForeignKey('address.Address', on_delete=models.PROTECT)

# In the parent serializer
class OrganizationSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    
    class Meta:
        model = Organization
        fields = ['id', 'name', 'address']
```

## Testing
- Unit tests cover model and serializer functionality
- Integration tests verify nested operations
- Factory available for test data generation

## Future Plans
See [Architectural Decisions](address_architectural_decisions.md) for future considerations including:
- Potential standalone endpoints
- Geocoding integration
- Address normalization 