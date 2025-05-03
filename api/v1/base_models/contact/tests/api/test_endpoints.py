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
        OrganizationMembershipFactory(user=test_user, organization=test_organization, role=admin_role)

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
        OrganizationMembershipFactory(user=test_user, organization=test_organization, role=admin_role)

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
        OrganizationMembershipFactory(user=test_user, organization=test_organization, role=member_role)

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
        OrganizationMembershipFactory(user=test_user, organization=test_organization, role=member_role)

        contact = ContactFactory(organization=test_organization)
        url = detail_url_fixture(contact.pk)
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['organization']['id'] == test_organization.pk

    def test_contact_validation_errors(self, authenticated_client, test_user, test_organization, list_create_url):
        """Test various validation errors (requires add perm for the check)"""
        # Assign role with add permission to attempt the POST
        admin_role = add_perms_to_role("Organization Admin", ["add_contact"])
        OrganizationMembershipFactory(user=test_user, organization=test_organization, role=admin_role)
        
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
        OrganizationMembershipFactory(user=test_user, organization=test_organization, role=member_role)

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
        OrganizationMembershipFactory(user=test_user, organization=test_organization, role=admin_role)
        
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