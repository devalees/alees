"""
Factories for product models.
"""
import factory
from factory.django import DjangoModelFactory
from api.v1.features.products.models import Product
from api.v1.base_models.organization.tests.factories import OrganizationFactory
from api.v1.base_models.common.category.tests.factories import CategoryFactory
from api.v1.base_models.common.uom.tests.factories import UnitOfMeasureFactory


class ProductFactory(DjangoModelFactory):
    """Factory for creating Product instances."""
    
    class Meta:
        model = Product
    
    name = factory.Sequence(lambda n: f"Test Product {n}")
    sku = factory.Sequence(lambda n: f"SKU{n:04d}")
    description = factory.Faker('paragraph')
    
    product_type = 'PHYSICAL'
    status = 'ACTIVE'
    
    # Foreign keys
    organization = factory.SubFactory(OrganizationFactory)
    category = factory.SubFactory(CategoryFactory, category_type='PRODUCT')
    base_uom = factory.SubFactory(UnitOfMeasureFactory)
    
    is_inventory_tracked = False
    is_purchasable = True
    is_sellable = True
    
    attributes = {}
    custom_fields = {}
    
    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Add tags to the product."""
        if not create:
            return
        
        if extracted:
            # If tags provided, add them
            for tag in extracted:
                self.tags.add(tag) 