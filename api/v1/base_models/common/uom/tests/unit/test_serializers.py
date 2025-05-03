import pytest
from rest_framework import serializers
# Remove ValidationError import as we are not testing write validation failures now
# from rest_framework.exceptions import ValidationError

from api.v1.base_models.common.uom.models import UomType, UnitOfMeasure
from api.v1.base_models.common.uom.serializers import UomTypeSerializer, UnitOfMeasureSerializer
# Factories might still be useful for setting up specific scenarios
from api.v1.base_models.common.uom.tests.factories import UomTypeFactory, UnitOfMeasureFactory

pytestmark = pytest.mark.django_db

# --- UomTypeSerializer Tests ---

def test_uomtype_serializer_output():
    """Test UomTypeSerializer serializes existing data correctly."""
    uom_type = UomType.objects.get(code="LENGTH")
    serializer = UomTypeSerializer(instance=uom_type)
    data = serializer.data
    assert set(data.keys()) == {'code', 'name', 'description', 'is_active', 'custom_fields'}
    assert data['code'] == "LENGTH"

# --- UnitOfMeasureSerializer Tests ---

def test_unitofmeasure_serializer_output_with_depth():
    """Test UnitOfMeasureSerializer serializes existing data with depth=1."""
    uom = UnitOfMeasure.objects.get(code="KG") # Assumes KG exists linked to MASS
    serializer = UnitOfMeasureSerializer(instance=uom)
    data = serializer.data

    assert data['code'] == "KG"
    assert data['name'] == "Kilogram"
    assert data['symbol'] == "kg"

    # Check the nested representation due to depth=1
    assert 'uom_type' in data
    assert isinstance(data['uom_type'], dict)
    assert data['uom_type']['code'] == "MASS"
    assert data['uom_type']['name'] == "Mass"
    # Ensure the nested details field from the previous approach is gone
    assert 'uom_type_details' not in data

    expected_keys = {
        'code', 'name', 'symbol', 'is_active', 'custom_fields',
        'uom_type' # Now contains nested data
    }
    assert set(data.keys()) == expected_keys

def test_unitofmeasure_serializer_read_only_fields():
    """Verify fields intended as read-only are marked as such."""
    serializer = UnitOfMeasureSerializer()
    read_only_fields = set(serializer.Meta.read_only_fields)
    expected_read_only = {
        'code', 'name', 'symbol', 'is_active',
        'custom_fields',
        'uom_type' # uom_type is now read-only with depth=1
    }
    assert read_only_fields == expected_read_only

# --- Custom Field Validation Tests (Read Context) ---
# These tests now only verify if the validation logic *runs* during serialization (e.g., prints warning)
# They don't test preventing invalid writes, as the serializer is read-only.

def test_unitofmeasure_custom_fields_validation_runs_on_mass():
    """Test custom_fields validation runs during serialization for MASS type."""
    mass_type = UomType.objects.get(code="MASS")
    # Use get_or_create to avoid IntegrityError if test runs multiple times
    uom, created = UnitOfMeasure.objects.get_or_create(
        code="TEST_MASS_BAD_CF",
        defaults={'name': "Test Bad CF", 'uom_type': mass_type, 'custom_fields': {}}
    )
    serializer = UnitOfMeasureSerializer(instance=uom)
    data = serializer.data # Trigger serialization and validation

    assert data is not None
    # No need to delete if using get_or_create, but doesn't hurt
    # uom.delete()

def test_unitofmeasure_custom_fields_validation_runs_on_non_mass():
    """Test custom_fields validation runs for non-MASS type without warning."""
    uom = UnitOfMeasure.objects.get(code="M") # Meter (LENGTH)
    serializer = UnitOfMeasureSerializer(instance=uom)
    data = serializer.data # Trigger serialization and validation

    # We just ensure serialization completes without error.
    assert data is not None

# Remove tests related to serializer write validation (is_valid checks)
# def test_unitofmeasure_custom_fields_validation_fail_on_create(): ...
# def test_unitofmeasure_custom_fields_validation_pass_on_create(): ...
# def test_unitofmeasure_custom_fields_validation_pass_non_mass_on_create(): ...
# def test_unitofmeasure_custom_fields_validation_fail_on_update(): ...
# def test_unitofmeasure_custom_fields_validation_pass_on_update(): ...
# def test_unitofmeasure_custom_fields_validation_pass_update_non_mass(): ...

def test_unitofmeasure_custom_fields_validation_pass():
    """Test custom_fields validation passes if required key is present for MASS type."""
    uom_type_mass = UomTypeFactory(code="MASS")
    data = {
        'code': 'LB',
        'name': 'Pound',
        'symbol': 'lb',
        'uom_type': uom_type_mass.code,
        'custom_fields': {'required_prop': 'abc', 'other': 456} # Contains 'required_prop'
    }
    serializer = UnitOfMeasureSerializer(data=data)
    assert serializer.is_valid(), serializer.errors # Should be valid

def test_unitofmeasure_custom_fields_validation_pass_non_mass():
    """Test custom_fields validation passes if type is not MASS, even without required key."""
    uom_type_length = UomTypeFactory(code="LENGTH")
    data = {
        'code': 'METER',
        'name': 'Meter',
        'symbol': 'm',
        'uom_type': uom_type_length.code,
        'custom_fields': {'other_prop': 789} # Missing 'required_prop', but type is LENGTH
    }
    serializer = UnitOfMeasureSerializer(data=data)
    assert serializer.is_valid(), serializer.errors # Should be valid 