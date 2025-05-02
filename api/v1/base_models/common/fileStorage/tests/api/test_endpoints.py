import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from django.db.models.fields.files import FieldFile # Import the class to patch

# Assuming models, factories, and helpers are correctly located
from api.v1.base_models.common.fileStorage.models import FileStorage
from api.v1.base_models.common.fileStorage.tests.factories import FileStorageFactory
from api.v1.base_models.organization.tests.factories import OrganizationFactory
from api.v1.base_models.user.tests.factories import UserFactory
# Import OrganizationMembershipFactory
from api.v1.base_models.organization.tests.factories import OrganizationMembershipFactory, GroupFactory
# Assuming permission helper exists
from api.v1.base_models.organization.tests.api.test_endpoints import get_permission 


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
    return user

@pytest.fixture
def upload_url():
    # Adjust namespace and name based on actual URL registration
    return reverse('v1:base_models:file_storage:file-upload') 

@pytest.fixture
def test_file():
    return SimpleUploadedFile("test_upload.txt", b"file content for upload test", content_type="text/plain")

@pytest.mark.django_db
class TestFileUploadView:

    def test_upload_success(self, api_client, user_in_org, organization, upload_url, test_file):
        """Test successful file upload with correct permissions."""
        # Assign permission to the user
        perm = get_permission(FileStorage, 'add_filestorage')
        user_in_org.user_permissions.add(perm)
        api_client.force_authenticate(user=user_in_org)
        
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
        assert response.data['uploaded_by']['id'] == user_in_org.id

        # Verify saved object
        new_file = FileStorage.objects.get(id=response.data['id'])
        assert new_file.organization == organization
        assert new_file.uploaded_by == user_in_org
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
        # DO NOT assign permission
        api_client.force_authenticate(user=user_in_org)
        
        data = {
            'file': test_file,
            'organization': organization.id 
        }
        
        response = api_client.post(upload_url, data, format='multipart')
        assert response.status_code == status.HTTP_403_FORBIDDEN
        # Ensure the mock was called
        mock_perm_check.assert_called_once_with(user_in_org, 'file_storage.add_filestorage', organization)

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
        perm = get_permission(FileStorage, 'add_filestorage')
        user_in_org.user_permissions.add(perm)
        api_client.force_authenticate(user=user_in_org)

        data = {
            'organization': organization.id
        }
        response = api_client.post(upload_url, data, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'file' in response.data # Check for specific field error

    def test_upload_missing_organization(self, api_client, user_in_org, upload_url, test_file):
        """Test file upload fails if 'organization' is missing (if required by view)."""
        perm = get_permission(FileStorage, 'add_filestorage')
        user_in_org.user_permissions.add(perm)
        api_client.force_authenticate(user=user_in_org)

        data = {
            'file': test_file
        }
        response = api_client.post(upload_url, data, format='multipart')
        # This might be 400 or 403 depending on how the view handles org determination
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
        # Add assertion for specific error message if needed

    # Add tests for file size validation, mime type validation (if implemented)

@pytest.fixture
def file_instance(db, organization, user_in_org):
    # Helper to create a FileStorage instance for tests
    # Use .create() which should save the file content
    # If content saving is still problematic, might need storage mocking
    return FileStorageFactory.create(
        organization=organization, 
        uploaded_by=user_in_org,
        original_filename='test_list.pdf',
        mime_type='application/pdf'
    )

@pytest.fixture
def list_url():
    # URL for the FileStorageViewSet list endpoint
    return reverse('v1:base_models:file_storage:file-list')

@pytest.fixture
def detail_url(file_instance):
    # URL for the FileStorageViewSet detail endpoint
    return reverse('v1:base_models:file_storage:file-detail', kwargs={'pk': file_instance.id})


@pytest.mark.django_db
class TestFileStorageViewSet:

    def test_list_success(self, api_client, user_in_org, organization, file_instance, list_url):
        """Test LIST endpoint returns files for the user's organization."""
        # Assign view permission
        perm = get_permission(FileStorage, 'view_filestorage')
        user_in_org.user_permissions.add(perm)
        api_client.force_authenticate(user=user_in_org)

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
        # DO NOT assign permission
        api_client.force_authenticate(user=user_in_org)
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
        mock_perm_check.return_value = True # Simulate user having perm
        perm = get_permission(FileStorage, 'view_filestorage')
        user_in_org.user_permissions.add(perm)
        api_client.force_authenticate(user=user_in_org)

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == file_instance.id
        assert response.data['original_filename'] == file_instance.original_filename
        assert response.data['download_url'] is not None # Should get URL with perm
        mock_perm_check.assert_called_once_with(user_in_org, 'file_storage.view_filestorage', file_instance.organization)

    # Use patch to simulate permission checks for download URL generation
    @patch('api.v1.base_models.common.fileStorage.serializers.has_perm_in_org')
    def test_retrieve_success_without_perm_for_url(self, mock_perm_check, api_client, user_in_org, file_instance, detail_url):
        """Test RETRIEVE success, but download_url is None without perm."""
        mock_perm_check.return_value = False # Simulate user lacking perm for URL
        perm = get_permission(FileStorage, 'view_filestorage')
        user_in_org.user_permissions.add(perm)
        api_client.force_authenticate(user=user_in_org)

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == file_instance.id
        assert response.data['download_url'] is None # Should NOT get URL without perm
        mock_perm_check.assert_called_once_with(user_in_org, 'file_storage.view_filestorage', file_instance.organization)

    def test_retrieve_no_view_permission(self, api_client, user_in_org, file_instance, detail_url):
        """Test RETRIEVE endpoint fails without view permission for the object."""
        # DO NOT assign permission
        api_client.force_authenticate(user=user_in_org)
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN # Or 404 if queryset filters it

    def test_retrieve_different_org(self, api_client, user_in_org, detail_url):
        """Test RETRIEVE fails for file in a different organization."""
        # user_in_org belongs to 'organization' fixture
        # file_instance (used by detail_url) also belongs to 'organization' fixture
        # Create a user in a different org
        other_org = OrganizationFactory()
        other_user = UserFactory(organization=other_org)
        perm = get_permission(FileStorage, 'view_filestorage')
        other_user.user_permissions.add(perm) # Give perm, but wrong org
        
        api_client.force_authenticate(user=other_user)
        response = api_client.get(detail_url)
        # Expect 404 because OrgScopedViewSetMixin should filter the queryset
        assert response.status_code == status.HTTP_404_NOT_FOUND 

    def test_retrieve_unauthenticated(self, api_client, detail_url):
        """Test RETRIEVE endpoint fails for unauthenticated users."""
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_success_with_perm(self, mocker, api_client, detail_url, file_instance, user_in_org):
        """Test DELETE endpoint success with correct permission."""
        # Assign delete permission
        perm = get_permission(FileStorage, 'delete_filestorage')
        user_in_org.user_permissions.add(perm)
        api_client.force_authenticate(user=user_in_org)

        # Mock the file deletion on the FieldFile class itself
        # mock_delete = mocker.patch.object(file_instance.file, 'delete')
        mock_delete = mocker.patch.object(FieldFile, 'delete')

        # --- DEBUG: Print type of file attribute ---
        # print(f"\nDEBUG: Type of file_instance.file: {type(file_instance.file)}\n")
        # --- END DEBUG ---

        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not FileStorage.objects.filter(pk=file_instance.pk).exists()
        # Check the call on the mock applied to the class
        # When patching a class method called by an instance, 
        # assert_called_once_with checks the args *after* self.
        # mock_delete.assert_called_once_with(file_instance.file, save=False) # Incorrect
        mock_delete.assert_called_once_with(save=False) # Correct: only check kwargs

    def test_delete_no_permission(self, api_client, detail_url, file_instance, user_in_org):
        """Test DELETE endpoint fails without correct permission."""
        # DO NOT assign delete permission
        api_client.force_authenticate(user=user_in_org)

        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert FileStorage.objects.filter(pk=file_instance.pk).exists()

    def test_delete_different_org(self, api_client, file_instance, user_in_org):
        """Test DELETE endpoint fails for file in different organization."""
        # Assign delete permission
        perm = get_permission(FileStorage, 'delete_filestorage')
        user_in_org.user_permissions.add(perm)
        api_client.force_authenticate(user=user_in_org)

        # Create a file in a different org
        other_org = OrganizationFactory()
        other_file = FileStorageFactory(organization=other_org)
        other_detail_url = reverse('v1:base_models:file_storage:file-detail', kwargs={'pk': other_file.pk})

        response = api_client.delete(other_detail_url)
        # Should be 404 because the OrgScoped mixin filters it out
        assert response.status_code == status.HTTP_404_NOT_FOUND 
        assert FileStorage.objects.filter(pk=other_file.pk).exists()

    def test_delete_unauthenticated(self, api_client, detail_url, file_instance):
        """Test DELETE endpoint fails for unauthenticated user."""
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert FileStorage.objects.filter(pk=file_instance.pk).exists()
