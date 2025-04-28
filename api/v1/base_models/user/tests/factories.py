import factory
from django.contrib.auth import get_user_model
from django.conf import settings
from ..models import UserProfile

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    is_active = True

class UserProfileFactory(factory.django.DjangoModelFactory):
    """Factory for creating UserProfile instances"""
    
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory, profile=None)  # Ensure no circular dependency
    job_title = factory.Faker('job')
    employee_id = factory.Sequence(lambda n: f'EMP{n:04d}')
    phone_number = factory.Faker('phone_number')
    manager = None  # Optional field
    date_of_birth = factory.Faker('date_of_birth')
    employment_type = factory.Faker('random_element', elements=['FULL_TIME', 'PART_TIME', 'CONTRACT'])
    profile_picture = None  # As specified in implementation steps
    language = settings.LANGUAGE_CODE
    timezone = settings.TIME_ZONE
    notification_preferences = factory.LazyFunction(dict)
    custom_fields = factory.LazyFunction(dict) 