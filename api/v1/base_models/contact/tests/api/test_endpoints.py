#!/usr/bin/python
# -*- coding: utf-8 -*-
import pytest
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from api.v1.base_models.contact.models import Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.contact.tests.factories import (
    ContactFactory,
    ContactEmailAddressFactory,
    ContactPhoneNumberFactory,
    ContactAddressFactory
)
from api.v1.base_models.organization.tests.factories import OrganizationFactory, OrganizationMembershipFactory
from api.v1.base_models.common.tag.tests.factories import TagFactory

User = get_user_model()

# --- Helper to add permissions to role ---
def add_perms_to_role(role_name, permissions_codenames):
    role, _ = Group.objects.get_or_create(name=role_name)
    ct = ContentType.objects.get_for_model(Contact)
    permissions = Permission.objects.filter(content_type=ct, codename__in=permissions_codenames)
    role.permissions.add(*permissions)
    return role
# --- End Helper --- 

# Use pytest fixtures for setup
@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user():
    return UserFactory()

@pytest.fixture
def test_organization():
    return OrganizationFactory()

@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client

@pytest.fixture
def list_create_url():
    return reverse("v1:base_models:contact:contact-list")

@pytest.fixture
def detail_url_fixture():
    def _detail_url(pk):
         return reverse('v1:base_models:contact:contact-detail', kwargs={'pk': pk})
    return _detail_url

@pytest.mark.django_db
class TestContactAPI:
    def test_create_contact_with_channels(self, authenticated_client, test_user, test_organization, list_create_url):
        """Test creating a contact with valid nested channel data."""
        # Assign role with add permission
        admin_role = add_perms_to_role("Organization Admin", ["add_contact", "view_contact", "change_contact", "delete_contact"])
        membership = OrganizationMembershipFactory(user=test_user, organization=test_organization)
        membership.roles.add(admin_role)

        # Valid nested data (provide full address or existing address_id)
        address_data = {
            "street_address_1": "1 Test Lane",
            "city": "Fixture City",
            "country": "US", 
            "postal_code": "12345"
        }
        data = {
            "first_name": "API Create",
            "last_name": "User",
            "organization_id": test_organization.pk,
            "email_addresses": [
                {"email": "create@example.com", "email_type": "work", "is_primary": True}
            ],
            "phone_numbers": [
                {"phone_number": "+15551234567", "phone_type": "mobile", "is_primary": True}
            ],
            "addresses": [
                {"address": address_data, "address_type": "billing", "is_primary": True}
            ]
        }
        response = authenticated_client.post(list_create_url, data, format='json')
        # Print response data on failure for debugging
        if response.status_code != status.HTTP_201_CREATED:
             print(f"Create Contact Response data: {response.data}") 
        assert response.status_code == status.HTTP_201_CREATED
        assert Contact.objects.count() == 1
        contact = Contact.objects.get(id=response.data['id'])
        assert contact.email_addresses.count() == 1
        assert contact.phone_numbers.count() == 1
        assert contact.addresses.count() == 1
        assert contact.first_name == "API Create"
        assert contact.organization == test_organization
        assert contact.email_addresses.first().email == "create@example.com"
        assert str(contact.phone_numbers.first().phone_number) == "+15551234567"
        assert contact.addresses.first().address.city == "Fixture City"

    def test_update_contact_primary_flags(self, authenticated_client, test_user, test_organization, detail_url_fixture):
        """Test updating primary flags for nested email/phone/address."""
        # Assign role with change permission
        admin_role = add_perms_to_role("Organization Admin", ["change_contact", "view_contact"])
        membership = OrganizationMembershipFactory(user=test_user, organization=test_organization)
        membership.roles.add(admin_role)

        contact = ContactFactory(organization=test_organization)
        email1 = ContactEmailAddressFactory(contact=contact, is_primary=True)
        email2 = ContactEmailAddressFactory(contact=contact, is_primary=False)
        url = detail_url_fixture(contact.pk)

        data = {
            "email_addresses": [
                {"id": email1.pk, "email": email1.email, "is_primary": False},
                {"id": email2.pk, "email": email2.email, "is_primary": True},
            ]
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK, response.data
        # Refresh instances from DB before asserting
        email1.refresh_from_db()
        email2.refresh_from_db()
        assert not email1.is_primary # Check email1 is now False
        assert email2.is_primary # Check email2 is now True

    def test_list_contacts_with_filtering(self, authenticated_client, test_user, test_organization, list_create_url):
        """Test listing contacts with various filters"""
        # Assign role with view permission
        member_role = add_perms_to_role("Member", ["view_contact"])
        membership = OrganizationMembershipFactory(user=test_user, organization=test_organization)
        membership.roles.add(member_role)

        # Create contacts within the user's org
        ContactFactory(organization=test_organization, first_name="Alice", last_name="Smith")
        ContactFactory.create_batch(3, organization=test_organization, first_name="TestFilter")
        ContactFactory.create_batch(2) # Contacts outside the user's org

        response = authenticated_client.get(list_create_url + '?first_name=TestFilter')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', [])
        assert len(results) == 3
        for item in results:
            assert item['organization']['id'] == test_organization.pk

    def test_contact_organization_link(self, authenticated_client, test_user, test_organization, detail_url_fixture):
        """Test that the organization is correctly linked and represented."""
        # Assign role with view permission
        member_role = add_perms_to_role("Member", ["view_contact"])
        membership = OrganizationMembershipFactory(user=test_user, organization=test_organization)
        membership.roles.add(member_role)

        contact = ContactFactory(organization=test_organization)
        url = detail_url_fixture(contact.pk)
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['organization']['id'] == test_organization.pk

    def test_contact_validation_errors(self, authenticated_client, test_user, test_organization, list_create_url):
        """Test various validation errors (requires add perm for the check)"""
        # Assign role with add permission to attempt the POST
        admin_role = add_perms_to_role("Organization Admin", ["add_contact"])
        membership = OrganizationMembershipFactory(user=test_user, organization=test_organization)
        membership.roles.add(admin_role)
        
        invalid_data = {
            'first_name': '',
            'organization_id': test_organization.pk
        }
        response = authenticated_client.post(list_create_url, invalid_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_contact_permissions(self, authenticated_client, test_user, test_organization, detail_url_fixture):
        """Test API permissions (user can't access other orgs due to scoping)"""
        # Need view permission in *some* org for the test to make sense
        member_role = add_perms_to_role("Member", ["view_contact"])
        membership = OrganizationMembershipFactory(user=test_user, organization=test_organization)
        membership.roles.add(member_role)

        # Create an org and user the test_user doesn't belong to
        other_org = OrganizationFactory()
        contact_in_other_org = ContactFactory(organization=other_org)
        detail_url = detail_url_fixture(contact_in_other_org.pk)

        # User shouldn't see contact in other org due to ViewSet scoping
        response = authenticated_client.get(detail_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_contact_custom_fields_and_tags(self, authenticated_client, test_user, test_organization, list_create_url):
        """Test custom fields and tags functionality"""
        # Assign role with add permission
        admin_role = add_perms_to_role("Organization Admin", ["add_contact"])
        membership = OrganizationMembershipFactory(user=test_user, organization=test_organization)
        membership.roles.add(admin_role)
        
        data = {
            "first_name": "Custom",
            "last_name": "Fields",
            "organization_id": test_organization.pk,
            "custom_fields": {'priority': 'high', 'ref_id': 123},
            "tags": ["customer", "potential"]
        }
        response = authenticated_client.post(list_create_url, data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Custom Fields/Tags - Status: {response.status_code}, Data: {response.data}")
        assert response.status_code == status.HTTP_201_CREATED
        contact = Contact.objects.get(pk=response.data['id'])
        assert contact.custom_fields['priority'] == 'high'
        assert 'customer' in [tag.name for tag in contact.tags.all()] 

    # --- Tag Filtering Tests ---
    # Ensure user has view permissions within the org for these tests

    def test_filter_contacts_by_single_tag(self, authenticated_client, test_user, test_organization, list_create_url):
        """Test filtering contacts by a single tag PK."""
        view_role = add_perms_to_role("Viewer", ["view_contact"])
        membership = OrganizationMembershipFactory(user=test_user, organization=test_organization)
        membership.roles.add(view_role)

        # Create tags
        lead_tag = TagFactory(name="lead")
        important_tag = TagFactory(name="important")
        customer_tag = TagFactory(name="customer")

        contact1 = ContactFactory(organization=test_organization)
        contact1.tags.add(lead_tag, important_tag)
        contact2 = ContactFactory(organization=test_organization)
        contact2.tags.add(customer_tag, important_tag)
        contact3 = ContactFactory(organization=test_organization) # No tags

        # Filter by lead_tag PK
        response = authenticated_client.get(list_create_url, {'tags': [lead_tag.pk]})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == contact1.id

    def test_filter_contacts_by_multiple_tags(self, authenticated_client, test_user, test_organization, list_create_url):
        """Test filtering contacts by multiple tag PKs (OR)."""
        view_role = add_perms_to_role("Viewer", ["view_contact"])
        membership = OrganizationMembershipFactory(user=test_user, organization=test_organization)
        membership.roles.add(view_role)

        # Create tags
        lead_tag = TagFactory(name="lead")
        vip_tag = TagFactory(name="vip")
        customer_tag = TagFactory(name="customer")
        prospect_tag = TagFactory(name="prospect")

        contact1 = ContactFactory(organization=test_organization)
        contact1.tags.add(lead_tag)
        contact2 = ContactFactory(organization=test_organization)
        contact2.tags.add(customer_tag, vip_tag)
        contact3 = ContactFactory(organization=test_organization)
        contact3.tags.add(prospect_tag)

        # Filter by lead_tag PK OR vip_tag PK
        response = authenticated_client.get(list_create_url, {'tags': [lead_tag.pk, vip_tag.pk]})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        result_ids = sorted([item['id'] for item in response.data['results']])
        assert result_ids == sorted([contact1.id, contact2.id])

    def test_filter_contacts_by_common_tag(self, authenticated_client, test_user, test_organization, list_create_url):
        """Test filtering contacts by a tag PK shared by multiple contacts."""
        view_role = add_perms_to_role("Viewer", ["view_contact"])
        membership = OrganizationMembershipFactory(user=test_user, organization=test_organization)
        membership.roles.add(view_role)

        # Create tags
        important_tag = TagFactory(name="important")
        lead_tag = TagFactory(name="lead")
        customer_tag = TagFactory(name="customer")
        prospect_tag = TagFactory(name="prospect")

        contact1 = ContactFactory(organization=test_organization)
        contact1.tags.add(lead_tag, important_tag)
        contact2 = ContactFactory(organization=test_organization)
        contact2.tags.add(customer_tag, important_tag)
        contact3 = ContactFactory(organization=test_organization)
        contact3.tags.add(prospect_tag)

        # Filter by important_tag PK
        response = authenticated_client.get(list_create_url, {'tags': [important_tag.pk]})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        result_ids = sorted([item['id'] for item in response.data['results']])
        assert result_ids == sorted([contact1.id, contact2.id])

    def test_filter_contacts_by_nonexistent_tag_pk(self, authenticated_client, test_user, test_organization, list_create_url):
        """Test filtering contacts by a tag PK that doesn't exist."""
        view_role = add_perms_to_role("Viewer", ["view_contact"])
        membership = OrganizationMembershipFactory(user=test_user, organization=test_organization)
        membership.roles.add(view_role)

        # Create a contact with a valid tag
        existing_tag = TagFactory(name="existing_tag")
        ContactFactory(organization=test_organization).tags.add(existing_tag)

        # Use a PK that is unlikely to exist (e.g., 99999)
        nonexistent_pk = 99999
        response = authenticated_client.get(list_create_url, {'tags': [nonexistent_pk]})

        # ModelMultipleChoiceFilter validates input PKs against its queryset.
        # Passing a non-existent PK correctly results in a 400 Bad Request.
        # Update assertion to expect 400.
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Optional: Check error message structure if needed
        # assert 'tags' in response.data
        # assert 'Select a valid choice' in str(response.data['tags']) 

    def test_create_contact_single_org_user_no_org_id(self, authenticated_client, test_user, test_organization, list_create_url):
        """Test creating a contact without organization_id for a single-organization user."""
        # Assign role with add permission
        admin_role = add_perms_to_role("Organization Admin", ["add_contact", "view_contact", "change_contact", "delete_contact"])
        membership = OrganizationMembershipFactory(user=test_user, organization=test_organization)
        membership.roles.add(admin_role)
        
        # Do not provide organization_id
        data = {
            "first_name": "Single",
            "last_name": "OrgUser",
            "email_addresses": [
                {"email": "single@example.com", "email_type": "work", "is_primary": True}
            ],
            "phone_numbers": [
                {"phone_number": "+15559876543", "phone_type": "mobile", "is_primary": True}
            ]
        }
        response = authenticated_client.post(list_create_url, data, format='json')
        
        # Print response data on failure for debugging
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Create Contact Response data: {response.data}")
            
        assert response.status_code == status.HTTP_201_CREATED
        assert Contact.objects.count() == 1
        contact = Contact.objects.get(id=response.data['id'])
        assert contact.first_name == "Single"
        assert contact.organization == test_organization  # Should use the user's only organization
        assert contact.email_addresses.first().email == "single@example.com" 

    def test_create_contact_multi_org_user_requires_org_id(self, authenticated_client, list_create_url):
        """Test that multi-organization users must provide an organization_id when creating a contact."""
        # Assign an "Organization Admin" role with all contact permissions
        role = Group.objects.get(name="Organization Admin")
        role.permissions.add(
            Permission.objects.get(codename="add_contact"),
            Permission.objects.get(codename="view_contact"),
            Permission.objects.get(codename="change_contact"),
            Permission.objects.get(codename="delete_contact"),
        )

        # Create memberships for two different organizations to make this a multi-org user
        user = UserFactory()
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        membership = OrganizationMembershipFactory(
            organization=org1,
            user=user,
            is_active=True
        )
        membership.roles.add(role)
        membership = OrganizationMembershipFactory(
            organization=org2,
            user=user,
            is_active=True
        )
        membership.roles.add(role)

        # Use api_client directly, not self.client
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        # Attempt to create a contact without specifying organization_id
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
        }
        response = api_client.post(list_create_url, data, format="json")

        # Should receive a 403 Forbidden with permission denied error
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "permission" in str(response.data).lower() 