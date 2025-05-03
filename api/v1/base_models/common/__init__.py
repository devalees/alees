# This file is intentionally empty to mark the directory as a Python package

from .apps import CommonConfig

# Removed imports from here

# Define default_app_config if needed (check Django version)
# default_app_config = 'api.v1.base_models.common.apps.CommonConfig'

# Ensure models from sub-modules are discoverable by Django's mechanisms (e.g., migrations)
# Although Django's model discovery should work via AppConfig, explicitly importing
# can sometimes resolve discovery issues, especially with nested structures.
# Reverted: Importing models here caused AppRegistryNotReady error.
# from .category.models import Category
# from .address.models import Address
# from .currency.models import Currency
# from .fileStorage.models import FileStorage
# from .status.models import StatusDefinition, StatusHistory
# from .uom.models import UnitOfMeasure, UnitOfMeasureConversion

# If using older Django versions or having discovery issues, defining default_app_config might help
# Check Django documentation for your version.
# default_app_config = 'api.v1.base_models.common.apps.CommonConfig' 