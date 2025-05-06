import os
import django
import sys
import uuid

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
django.setup()

# Now import Django models after setup
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from api.v1.base_models.organization.models import Organization, OrganizationMembership
from api.v1.base_models.organization.tests.factories import OrganizationFactory, GroupFactory
from api.v1.base_models.user.tests.factories import UserFactory
from django.contrib.auth.models import Permission
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

# Create a test user with appropriate organization membership and permission
User = get_user_model()

# Generate a unique username
unique_username = f"testuser_{uuid.uuid4().hex[:8]}"
print(f"Creating user with username: {unique_username}")

# Create org and user
org = OrganizationFactory(name='Test Org')
user = UserFactory(username=unique_username, email=f"{unique_username}@example.com")
role = GroupFactory(name='File Upload Role')

# Add file permission to the role
perm = Permission.objects.get(codename='add_filestorage')
role.permissions.add(perm)

# Create membership and add role
membership = OrganizationMembership.objects.create(
    user=user,
    organization=org,
    is_active=True
)
membership.roles.add(role)

# Set password for login
user.set_password('password123')
user.save()

# Verify user has the right permission
from core.rbac.permissions import has_perm_in_org
has_perm = has_perm_in_org(user, 'add_filestorage', org)
print(f'User has add_filestorage permission: {has_perm}')

# Use API client
client = APIClient()

# Get token for user
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

# Set token for authentication
client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

print(f'Authentication token obtained and set for user: {user.username}')

# Create a test file
test_file = SimpleUploadedFile(
    'test_upload.txt',
    b'file content for upload test',
    content_type='text/plain'
)

# Upload file
response = client.post(
    '/api/v1/file-storage/files/upload/',
    {'file': test_file, 'organization': org.id},
    format='multipart'
)

print(f'Upload response status: {response.status_code}')
if response.status_code == 201:
    print('File upload successful!')
    print(f'File ID: {response.data["id"]}')
    print(f'Original filename: {response.data["original_filename"]}')
else:
    print(f'Upload failed: {response.data}') 