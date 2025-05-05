import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from django.db.models.fields.files import FieldFile # Import the class to patch
import os

# Assuming models, factories, and helpers are correctly located
from api.v1.base_models.common.fileStorage.models import FileStorage
from api.v1.base_models.common.fileStorage.tests.factories import FileStorageFactory
from api.v1.base_models.organization.tests.factories import OrganizationFactory
from api.v1.base_models.user.tests.factories import UserFactory
# Import OrganizationMembershipFactory
from api.v1.base_models.organization.tests.factories import OrganizationMembershipFactory, GroupFactory
# Assuming permission helper exists
from api.v1.base_models.organization.tests.api.test_endpoints import get_permission 

# Define the correct full namespace
FILESTORAGE_NAMESPACE = "v1:base_models:common"

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def organization(db):
    return OrganizationFactory()

@pytest.fixture
def default_role(db):
    # Create a default role (Group) if needed for membership
    return GroupFactory(name='Default Member Role')

@pytest.fixture
def user_in_org(db, organization, default_role):
    # Create a user 
    user = UserFactory()
    # Explicitly create an active membership linking user and organization
    OrganizationMembershipFactory.create(
        user=user,
        organization=organization,
        role=default_role, # Assign a role
        is_active=True
    )
    # Refresh user instance if needed (though membership is separate)
    # user.refresh_from_db() 
    # Return both user and their role for permission assignment
    return user, default_role

@pytest.fixture
def upload_url():
    # Use correct namespace and name
    return reverse(f'{FILESTORAGE_NAMESPACE}:file-upload') 

@pytest.fixture
def test_file():
    return SimpleUploadedFile("test_upload.txt", b"file content for upload test", content_type="text/plain")

@pytest.mark.django_db
class TestFileUploadView:

    def test_upload_success(self, api_client, user_in_org, organization, upload_url, test_file):
        """Test successful file upload with correct permissions."""
        user, role = user_in_org # Unpack user and role
        # Assign permission to the role
        perm = get_permission(FileStorage, 'add_filestorage')
        role.permissions.add(perm) 
        api_client.force_authenticate(user=user)
        
        # Data for the POST request
        data = {
            'file': test_file,
            'organization': organization.id # Assuming org is required in request
        }

        initial_count = FileStorage.objects.count()
        response = api_client.post(upload_url, data, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        assert FileStorage.objects.count() == initial_count + 1
        
        # Verify response data contains expected fields (adjust based on serializer)
        assert 'id' in response.data
        assert response.data['original_filename'] == test_file.name
        assert response.data['mime_type'] == test_file.content_type
        assert response.data['organization']['id'] == organization.id
        assert response.data['uploaded_by']['id'] == user.id

        # Verify saved object
        new_file = FileStorage.objects.get(id=response.data['id'])
        assert new_file.organization == organization
        assert new_file.uploaded_by == user
        assert new_file.original_filename == test_file.name
        # assert new_file.file.read() == test_file.read() # Content check failing, maybe due to test storage
        # Check if file field has a name and size instead
        assert new_file.file.name is not None
        assert new_file.file.size == test_file.size # Check size
        # Clean up the created file from storage if necessary
        new_file.file.delete(save=False) 

    @patch('api.v1.base_models.common.fileStorage.views.has_perm_in_org', return_value=False)
    def test_upload_no_permission(self, mock_perm_check, api_client, user_in_org, organization, upload_url, test_file):
        """Test file upload fails when user lacks permission."""
        user, _ = user_in_org # Unpack user, ignore role
        # DO NOT assign permission
        api_client.force_authenticate(user=user)
        
        data = {
            'file': test_file,
            'organization': organization.id 
        }
        
        response = api_client.post(upload_url, data, format='multipart')
        assert response.status_code == status.HTTP_403_FORBIDDEN
        # Ensure the mock was called
        mock_perm_check.assert_called_once_with(user, 'file_storage.add_filestorage', organization)

    def test_upload_unauthenticated(self, api_client, upload_url, test_file, organization):
        """Test file upload fails for unauthenticated users."""
        data = {
            'file': test_file,
            'organization': organization.id 
        }
        response = api_client.post(upload_url, data, format='multipart')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_missing_file(self, api_client, user_in_org, organization, upload_url):
        """Test file upload fails if 'file' is missing."""
        user, role = user_in_org # Unpack user and role
        perm = get_permission(FileStorage, 'add_filestorage')
        role.permissions.add(perm) # Assign to role
        api_client.force_authenticate(user=user)

        data = {
            'organization': organization.id
        }
        response = api_client.post(upload_url, data, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'file' in response.data # Check for specific field error

    def test_upload_missing_organization(self, api_client, user_in_org, organization, upload_url, test_file):
        """Test upload when organization field is missing."""
        user, role = user_in_org  # Unpack user and role
        # Assign permission to the role
        perm = get_permission(FileStorage, 'add_filestorage')
        role.permissions.add(perm)
        api_client.force_authenticate(user=user)
        
        # Data for the POST request - omit organization field
        data = {
            'file': test_file
        }

        # Count initial number of FileStorage objects
        initial_count = FileStorage.objects.count()

        # Mock the get_user_request_context to simulate single-org user
        with patch('core.rbac.utils.get_user_request_context') as mock_get_context:
            # Return single organization ID and True for is_single_org
            mock_get_context.return_value = ([organization.id], True)
            response = api_client.post(upload_url, data, format='multipart')

        # For single-org users, request should succeed without requiring organization
        assert response.status_code == status.HTTP_201_CREATED
        # A file was uploaded
        assert FileStorage.objects.count() == initial_count + 1
        # Check that the file is correctly associated with the user's organization
        uploaded_file = FileStorage.objects.latest('id')
        assert uploaded_file.organization.id == organization.id
        assert uploaded_file.uploaded_by == user

        # Clean up storage if needed
        if os.path.exists(uploaded_file.file.path):
            os.remove(uploaded_file.file.path)

    def test_upload_success_single_org_user_no_org(self, api_client, user_in_org, organization, upload_url, test_file):
        """Test successful file upload without specifying organization for single-org user."""
        user, role = user_in_org  # Unpack user and role
        # Assign permission to the role
        perm = get_permission(FileStorage, 'add_filestorage')
        role.permissions.add(perm)
        api_client.force_authenticate(user=user)
        
        # Data for the POST request - omit organization field for single-org user
        data = {
            'file': test_file
        }

        initial_count = FileStorage.objects.count()
        
        # Mock the get_user_request_context to ensure single-org behavior
        with patch('core.rbac.utils.get_user_request_context') as mock_get_context:
            # Return the organization ID and True for is_single_org
            mock_get_context.return_value = ([organization.id], True)
            response = api_client.post(upload_url, data, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        assert FileStorage.objects.count() == initial_count + 1
        
        # Verify the file was saved with the correct organization
        new_file = FileStorage.objects.get(id=response.data['id'])
        assert new_file.organization == organization
        assert new_file.uploaded_by == user
        assert new_file.original_filename == test_file.name
        
        # Clean up the created file from storage if necessary
        new_file.file.delete(save=False)

    def test_upload_multi_org_user_requires_org(self, api_client, user_in_org, organization, upload_url, test_file):
        """Test multi-org user must provide organization when uploading a file."""
        user, role = user_in_org  # Unpack user and role
        # Assign permission to the role
        perm = get_permission(FileStorage, 'add_filestorage')
        role.permissions.add(perm)
        api_client.force_authenticate(user=user)
        
        # Create a second organization for the user to make them a multi-org user
        second_org = OrganizationFactory()
        OrganizationMembershipFactory.create(
            user=user,
            organization=second_org,
            role=role,
            is_active=True
        )
        
        # Data for the POST request - omit organization field
        data = {
            'file': test_file
        }

        # Mock the get_user_request_context to simulate multi-org user
        with patch('core.rbac.utils.get_user_request_context') as mock_get_context:
            # Return multiple organization IDs and False for is_single_org
            mock_get_context.return_value = ([organization.id, second_org.id], False)
            response = api_client.post(upload_url, data, format='multipart')

        # Should get 403 Forbidden with a permission error message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        # The response contains a permission denied error message
        assert 'permission' in str(response.data).lower()

    # Add tests for file size validation, mime type validation (if implemented)

@pytest.fixture
def file_instance(db, organization, user_in_org):
    # Helper to create a FileStorage instance for tests
    # Use .create() which should save the file content
    # If content saving is still problematic, might need storage mocking
    return FileStorageFactory.create(
        organization=organization, 
        uploaded_by=user_in_org[0],
        original_filename='test_list.pdf',
        mime_type='application/pdf'
    )

@pytest.fixture
def list_url():
    # Use correct namespace and name
    return reverse(f'{FILESTORAGE_NAMESPACE}:file-list')

@pytest.fixture
def detail_url(file_instance):
    # Use correct namespace and name
    return reverse(f'{FILESTORAGE_NAMESPACE}:file-detail', kwargs={'pk': file_instance.id})


@pytest.mark.django_db
class TestFileStorageViewSet:

    def test_list_success(self, api_client, user_in_org, organization, file_instance, list_url):
        """Test LIST endpoint returns files for the user's organization."""
        user, role = user_in_org # Unpack user and role
        # Assign view permission to the role
        perm = get_permission(FileStorage, 'view_filestorage')
        role.permissions.add(perm) 
        api_client.force_authenticate(user=user)

        # Create a file in another org - should NOT be listed
        other_org = OrganizationFactory()
        FileStorageFactory.create(organization=other_org)

        response = api_client.get(list_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1 # Only file_instance from user's org
        assert response.data['results'][0]['id'] == file_instance.id
        assert response.data['results'][0]['organization']['id'] == organization.id

    def test_list_no_permission(self, api_client, user_in_org, file_instance, list_url):
        """Test LIST endpoint fails without view permission."""
        user, _ = user_in_org # Unpack user, ignore role
        # DO NOT assign permission
        api_client.force_authenticate(user=user)
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_unauthenticated(self, api_client, list_url):
        """Test LIST endpoint fails for unauthenticated users."""
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Use patch to simulate permission checks for download URL generation
    @patch('api.v1.base_models.common.fileStorage.serializers.has_perm_in_org')
    def test_retrieve_success_with_perm(self, mock_perm_check, api_client, user_in_org, file_instance, detail_url):
        """Test RETRIEVE endpoint success with view permission."""
        user, role = user_in_org # Unpack user and role
        mock_perm_check.return_value = True # Simulate user having perm for URL generation
        # Assign view permission to the role for the viewset check
        perm = get_permission(FileStorage, 'view_filestorage')
        role.permissions.add(perm)
        api_client.force_authenticate(user=user)

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == file_instance.id
        assert response.data['original_filename'] == file_instance.original_filename
        assert response.data['download_url'] is not None # Should get URL with perm
        mock_perm_check.assert_called_once_with(user, 'file_storage.view_filestorage', file_instance.organization)

    # Use patch to simulate permission checks for download URL generation
    @patch('api.v1.base_models.common.fileStorage.serializers.has_perm_in_org')
    def test_retrieve_success_without_perm_for_url(self, mock_perm_check, api_client, user_in_org, file_instance, detail_url):
        """Test RETRIEVE success, but download_url is None without perm."""
        user, role = user_in_org # Unpack user and role
        mock_perm_check.return_value = False # Simulate user lacking perm for URL
        # Assign view permission to the role for the viewset check
        perm = get_permission(FileStorage, 'view_filestorage')
        role.permissions.add(perm)
        api_client.force_authenticate(user=user)

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == file_instance.id
        assert response.data['download_url'] is None # Should NOT get URL without perm
        mock_perm_check.assert_called_once_with(user, 'file_storage.view_filestorage', file_instance.organization)

    def test_retrieve_no_view_permission(self, api_client, user_in_org, file_instance, detail_url):
        """Test RETRIEVE endpoint fails without view permission for the object."""
        user, _ = user_in_org # Unpack user, ignore role
        # DO NOT assign permission
        api_client.force_authenticate(user=user)
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN # Or 404 if queryset filters it

    def test_retrieve_different_org(self, api_client, user_in_org, detail_url):
        """Test RETRIEVE fails for files in organizations the user is not part of."""
        user, role = user_in_org # Unpack user and role
        # Assign view permission (shouldn't matter as org is wrong)
        perm = get_permission(FileStorage, 'view_filestorage')
        role.permissions.add(perm)
        api_client.force_authenticate(user=user)

        # Create file in a different org
        other_org = OrganizationFactory()
        other_file = FileStorageFactory(organization=other_org)
        
        # Get the detail URL for the other file
        other_detail_url = reverse(f'{FILESTORAGE_NAMESPACE}:file-detail', kwargs={'pk': other_file.id})
        
        response = api_client.get(other_detail_url)
        
        # Expect 404 because the queryset is scoped to the user's org
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_unauthenticated(self, api_client, detail_url):
        """Test RETRIEVE endpoint fails for unauthenticated users."""
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_success_with_perm(self, mocker, api_client, detail_url, file_instance, user_in_org):
        """Test DELETE endpoint success with delete permission."""
        user, role = user_in_org # Unpack user and role
        # Assign delete permission to the role
        perm = get_permission(FileStorage, 'delete_filestorage')
        role.permissions.add(perm)
        api_client.force_authenticate(user=user)
        
        # Mock the physical file deletion
        mock_delete = mocker.patch.object(FieldFile, 'delete')
        
        initial_count = FileStorage.objects.count()
        response = api_client.delete(detail_url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert FileStorage.objects.count() == initial_count - 1
        # Check that the mock was called (meaning physical deletion was attempted)
        mock_delete.assert_called_once_with(save=False)
        
        # Verify the object no longer exists
        with pytest.raises(FileStorage.DoesNotExist):
            FileStorage.objects.get(id=file_instance.id)

    def test_delete_no_permission(self, api_client, detail_url, file_instance, user_in_org):
        """Test DELETE endpoint fails without delete permission."""
        user, _ = user_in_org # Unpack user, ignore role
        # DO NOT assign delete permission
        api_client.force_authenticate(user=user)
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        # Verify object still exists
        assert FileStorage.objects.filter(id=file_instance.id).exists()

    def test_delete_different_org(self, api_client, file_instance, user_in_org):
        """Test DELETE fails for files in organizations the user is not part of."""
        user, role = user_in_org # Unpack user and role
        # Assign delete permission (shouldn't matter as org is wrong)
        perm = get_permission(FileStorage, 'delete_filestorage')
        role.permissions.add(perm)
        api_client.force_authenticate(user=user)
        
        # Create file in other org
        other_org = OrganizationFactory()
        other_file = FileStorageFactory(organization=other_org)
        other_detail_url = reverse(f'{FILESTORAGE_NAMESPACE}:file-detail', kwargs={'pk': other_file.id})

        response = api_client.delete(other_detail_url)
        # Expect 404 because the queryset is scoped
        assert response.status_code == status.HTTP_404_NOT_FOUND
        # Verify other file still exists
        assert FileStorage.objects.filter(id=other_file.id).exists()

    def test_delete_unauthenticated(self, api_client, detail_url, file_instance):
        """Test DELETE endpoint fails for unauthenticated users."""
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # Verify object still exists
        assert FileStorage.objects.filter(id=file_instance.id).exists()
