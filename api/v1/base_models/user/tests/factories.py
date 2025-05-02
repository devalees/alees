import factory
from django.contrib.auth import get_user_model
from django.conf import settings
from ..models import UserProfile

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        exclude = ('organization',)

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    is_active = True

    organization = factory.SubFactory('api.v1.base_models.organization.tests.factories.OrganizationFactory')

    @factory.post_generation
    def create_profile(self, create, extracted, **kwargs):
        """Creates UserProfile only if using 'create' strategy and one doesn't exist."""
        if not create:
            # Simple build, do nothing.
            return
        
        # Check if a profile already exists for this user
        # Assumes UserProfile has a related_name like 'profile' or default 'userprofile'
        profile_rel_name = UserProfile.user.field.related_query_name()
        if not hasattr(self, profile_rel_name) or getattr(self, profile_rel_name) is None:
            # If no profile exists, create one using UserProfileFactory
            # Pass the user and organization down explicitly
            UserProfileFactory.create(
                user=self,
                organization=self.organization, # Use the org associated with UserFactory
                **kwargs # Pass any extra kwargs meant for the profile
            )
        # If extracted is True (i.e., profile=some_profile passed to UserFactory), 
        # factory-boy handles associating it, so we don't need to do anything here.

class UserProfileFactory(factory.django.DjangoModelFactory):
    """Factory for creating UserProfile instances"""
    
    class Meta:
        model = UserProfile
        exclude = ('organization',)

    organization = factory.SubFactory('api.v1.base_models.organization.tests.factories.OrganizationFactory')
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