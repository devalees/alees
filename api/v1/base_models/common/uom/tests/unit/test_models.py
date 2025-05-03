import pytest
from django.db import IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError

from api.v1.base_models.common.uom.models import UomType, UnitOfMeasure
# Assuming factories are primarily for API/integration tests or specific scenarios now
# from .factories import UomTypeFactory, UnitOfMeasureFactory

pytestmark = pytest.mark.django_db

# --- UomType Tests ---

def test_uomtype_retrieve_existing():
    """Test retrieving a UomType created by the migration."""
    # Assumes 'LENGTH' was created by the 0005 migration
    uom_type = UomType.objects.get(code="LENGTH")
    assert uom_type.pk == "LENGTH"
    assert uom_type.name == "Length"
    assert uom_type.is_active is True
    # Timestamps/Audit fields might be set depending on migration run context
    assert isinstance(uom_type.created_at, timezone.datetime)
    assert isinstance(uom_type.updated_at, timezone.datetime)

def test_uomtype_str_representation():
    """Test the __str__ method of UomType using existing data."""
    uom_type = UomType.objects.get(code="MASS") # Assumes MASS exists
    assert str(uom_type) == "Mass"

def test_uomtype_code_primary_key_violation():
    """Test creating a type with an existing code fails."""
    # 'VOLUME' should exist from migration
    with pytest.raises(IntegrityError):
        UomType.objects.create(code="VOLUME", name="Another Volume")

def test_uomtype_name_unique_violation():
    """Test creating a type with an existing name fails."""
    # 'Time' name should exist from migration (code='TIME')
    with pytest.raises(IntegrityError):
        UomType.objects.create(code="DURATION", name="Time") # Different code, same name

def test_uomtype_defaults_retrieved():
    """Test default values for fields like is_active on retrieved instance."""
    uom_type = UomType.objects.get(code="COUNT") # Assumes COUNT exists
    assert uom_type.is_active is True
    # Cannot reliably test custom_fields default on retrieved migrated data
    # assert uom_type.custom_fields == {}

def test_uomtype_update():
    """Test updating an existing UomType."""
    uom_type = UomType.objects.get(code="AREA") # Assumes AREA exists
    old_updated_at = uom_type.updated_at
    uom_type.description = "Updated Description"
    uom_type.is_active = False
    uom_type.save()
    uom_type.refresh_from_db()

    assert uom_type.description == "Updated Description"
    assert uom_type.is_active is False
    assert uom_type.updated_at > old_updated_at

# --- UnitOfMeasure Tests ---

def test_unitofmeasure_retrieve_existing():
    """Test retrieving a UnitOfMeasure created by the migration."""
    # Assumes 'M' (Meter) was created by migration, linked to 'LENGTH'
    uom = UnitOfMeasure.objects.get(code="M")
    assert uom.pk == "M"
    assert uom.name == "Meter"
    assert uom.symbol == "m"
    assert uom.uom_type.code == "LENGTH"
    assert uom.is_active is True
    assert isinstance(uom.created_at, timezone.datetime)
    assert isinstance(uom.updated_at, timezone.datetime)

def test_unitofmeasure_str_representation():
    """Test the __str__ method using existing data."""
    uom = UnitOfMeasure.objects.get(code="KG") # Assumes KG exists
    assert str(uom) == "Kilogram"

def test_unitofmeasure_code_primary_key_violation():
    """Test creating a unit with an existing code fails."""
    uom_type = UomType.objects.get(code="VOLUME") # Get existing type
    # 'L' should exist from migration
    with pytest.raises(IntegrityError):
        UnitOfMeasure.objects.create(code="L", name="Another Liter", uom_type=uom_type)

def test_unitofmeasure_name_unique_violation():
    """Test creating a unit with an existing name fails."""
    uom_type_time = UomType.objects.get(code="TIME")
    uom_type_freq = UomType.objects.create(code="FREQUENCY", name="Frequency") # Create a new type
    # 'Second' name exists (code='SEC')
    with pytest.raises(IntegrityError):
        UnitOfMeasure.objects.create(code="HERTZ", name="Second", uom_type=uom_type_freq)

def test_unitofmeasure_foreign_key_link():
    """Test the foreign key relationship using existing data."""
    uom = UnitOfMeasure.objects.get(code="EA") # Assumes EA exists
    uom_type = UomType.objects.get(code="COUNT")
    assert uom.uom_type == uom_type
    assert uom_type.units.filter(code="EA").exists()

def test_unitofmeasure_fk_protection():
    """Test that UomType cannot be deleted if referenced (using existing data)."""
    uom_type = UomType.objects.get(code="AREA") # Assumes SQM exists linked to AREA
    assert UnitOfMeasure.objects.filter(uom_type=uom_type).exists()
    with pytest.raises(IntegrityError): # Django raises IntegrityError on protected FK deletion
        uom_type.delete()

def test_unitofmeasure_update():
    """Test updating an existing UnitOfMeasure."""
    uom = UnitOfMeasure.objects.get(code="J") # Assumes Joule exists
    old_updated_at = uom.updated_at
    uom.symbol = "joule"
    uom.is_active = False
    uom.save()
    uom.refresh_from_db()

    assert uom.symbol == "joule"
    assert uom.is_active is False
    assert uom.updated_at > old_updated_at

# Test creating NEW types/units if needed for specific scenarios
def test_create_new_uom_type_and_unit():
    """Test creating a completely new type and unit."""
    new_type_code = "CUSTOMTYPE"
    new_type_name = "Custom Type"
    new_unit_code = "CUSTOMUNIT"
    new_unit_name = "Custom Unit"

    assert not UomType.objects.filter(code=new_type_code).exists()
    assert not UnitOfMeasure.objects.filter(code=new_unit_code).exists()

    new_type = UomType.objects.create(code=new_type_code, name=new_type_name)
    new_unit = UnitOfMeasure.objects.create(
        code=new_unit_code,
        name=new_unit_name,
        uom_type=new_type,
        symbol="cust"
    )

    assert new_unit.uom_type == new_type
    assert new_unit.name == new_unit_name
    assert new_type.units.count() == 1 