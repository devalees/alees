"""
Example: Implementing RBAC in a new Invoice app
This example demonstrates how to apply organization-aware RBAC to a new Invoice module
"""

# models.py
from django.db import models
from core.models import AuditableModel, OrganizationScoped
from django.conf import settings


class Invoice(OrganizationScoped, AuditableModel):
    """Invoice model with organization scoping."""
    invoice_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    due_date = models.DateField()
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    
    class Meta:
        permissions = [
            ('generate_pdf', 'Can generate PDF invoice'),
            ('mark_as_paid', 'Can mark invoice as paid'),
            ('send_invoice', 'Can send invoice to customer'),
        ]


class InvoiceItem(models.Model):
    """Line item for an invoice."""
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def subtotal(self):
        return self.quantity * self.unit_price


# serializers.py
from rest_framework import serializers
from core.serializers.mixins import OrganizationScopedSerializerMixin
from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for invoice line items."""
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = InvoiceItem
        fields = ['id', 'description', 'quantity', 'unit_price', 'subtotal']


class InvoiceSerializer(OrganizationScopedSerializerMixin, serializers.ModelSerializer):
    """Organization-aware serializer for invoices."""
    items = InvoiceItemSerializer(many=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'date', 'due_date', 'customer', 
            'total_amount', 'status', 'items', 'created_at', 'updated_at', 'organization'
        ]
        read_only_fields = ['total_amount']
    
    def create(self, validated_data):
        """Create invoice with nested items."""
        items_data = validated_data.pop('items', [])
        
        # Create the invoice using parent's create (handles organization)
        invoice = super().create(validated_data)
        
        # Create invoice items
        self.create_invoice_items(invoice, items_data)
        
        # Calculate total
        self.update_invoice_total(invoice)
        
        return invoice
    
    def update(self, instance, validated_data):
        """Update invoice with nested items."""
        items_data = validated_data.pop('items', None)
        
        # Update the invoice
        instance = super().update(instance, validated_data)
        
        # Update items if provided
        if items_data is not None:
            self.update_invoice_items(instance, items_data)
            self.update_invoice_total(instance)
        
        return instance
    
    def create_invoice_items(self, invoice, items_data):
        """Create invoice items for a new invoice."""
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
    
    def update_invoice_items(self, invoice, items_data):
        """Update invoice items for an existing invoice."""
        # Clear existing items and create new ones
        invoice.items.all().delete()
        self.create_invoice_items(invoice, items_data)
    
    def update_invoice_total(self, invoice):
        """Update the total amount of the invoice based on items."""
        total = sum(item.subtotal for item in invoice.items.all())
        invoice.total_amount = total
        invoice.save()


# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from core.viewsets.mixins import OrganizationScopedViewSetMixin
from core.rbac.drf_permissions import HasModelPermissionInOrg
from core.rbac.permissions import has_perm_in_org
from .models import Invoice
from .serializers import InvoiceSerializer
import logging

logger = logging.getLogger(__name__)


class InvoiceViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    Organization-aware ViewSet for invoices.
    Provides CRUD operations and additional actions with permission checks.
    """
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filterset_fields = ['status', 'customer', 'date', 'due_date']
    ordering_fields = ['date', 'due_date', 'total_amount', 'status']
    ordering = ['-date']
    
    def get_permissions(self):
        """Set permissions based on the action."""
        return [HasModelPermissionInOrg()]
    
    def perform_create(self, serializer):
        """Handle organization assignment when creating an invoice."""
        user = self.request.user
        logger.info(f"Creating invoice by user {user.username} (superuser: {user.is_superuser})")
        
        # For simplicity, use default organization handling
        # The OrganizationScopedSerializerMixin will handle this for most cases
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def send_to_customer(self, request, pk=None):
        """Send the invoice to the customer."""
        invoice = self.get_object()  # This will check object permissions
        
        # Explicit permission check for sending invoice
        if not has_perm_in_org(request.user, 'send_invoice', invoice.organization_id):
            raise PermissionDenied("You don't have permission to send invoices")
        
        # Check if invoice is in proper state
        if invoice.status != 'draft':
            return Response(
                {"detail": "Only draft invoices can be sent"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send the invoice (simplified for example)
        invoice.status = 'sent'
        invoice.save()
        
        return Response({"status": "Invoice sent successfully"})
    
    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        """Mark the invoice as paid."""
        invoice = self.get_object()
        
        # Explicit permission check for marking as paid
        if not has_perm_in_org(request.user, 'mark_as_paid', invoice.organization_id):
            raise PermissionDenied("You don't have permission to mark invoices as paid")
        
        # Check if invoice is in proper state
        if invoice.status not in ['sent', 'overdue']:
            return Response(
                {"detail": "Only sent or overdue invoices can be marked as paid"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as paid
        invoice.status = 'paid'
        invoice.save()
        
        return Response({"status": "Invoice marked as paid"})


# Example test case
# tests/test_invoice_permissions.py
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from api.v1.base_models.invoice.models import Invoice
from api.v1.organization.models import Organization

User = get_user_model()


class TestInvoicePermissions:
    """Test RBAC permissions for the Invoice app."""
    
    @pytest.fixture
    def setup_data(self, db):
        """Set up test data."""
        # Create organizations
        org1 = Organization.objects.create(name="Test Org 1")
        org2 = Organization.objects.create(name="Test Org 2")
        
        # Create roles
        admin_role = Group.objects.get(name="Admin")
        accountant_role = Group.objects.get(name="Accountant")
        viewer_role = Group.objects.get(name="Viewer")
        
        # Create users with different roles
        admin_user = User.objects.create_user(username="admin_user", password="password")
        admin_user.organization_memberships.create(organization=org1, is_active=True, role=admin_role)
        
        accountant_user = User.objects.create_user(username="accountant_user", password="password")
        accountant_user.organization_memberships.create(organization=org1, is_active=True, role=accountant_role)
        
        viewer_user = User.objects.create_user(username="viewer_user", password="password")
        viewer_user.organization_memberships.create(organization=org1, is_active=True, role=viewer_role)
        
        # Multi-org user
        multi_org_user = User.objects.create_user(username="multi_org_user", password="password")
        multi_org_user.organization_memberships.create(organization=org1, is_active=True, role=viewer_role)
        multi_org_user.organization_memberships.create(organization=org2, is_active=True, role=accountant_role)
        
        # Create test invoices
        invoice1 = Invoice.objects.create(
            invoice_number="INV-001",
            date="2023-01-01",
            due_date="2023-01-31",
            customer_id=1,  # Assuming a customer exists
            total_amount=100.00,
            status="draft",
            organization=org1
        )
        
        invoice2 = Invoice.objects.create(
            invoice_number="INV-002",
            date="2023-02-01",
            due_date="2023-02-28",
            customer_id=1,
            total_amount=200.00,
            status="sent",
            organization=org2
        )
        
        return {
            'org1': org1, 
            'org2': org2, 
            'admin_user': admin_user,
            'accountant_user': accountant_user, 
            'viewer_user': viewer_user,
            'multi_org_user': multi_org_user,
            'invoice1': invoice1,
            'invoice2': invoice2
        }
    
    def test_list_invoices_organization_scoped(self, setup_data):
        """Test that users can only see invoices from their organizations."""
        client = APIClient()
        
        # Admin user should see org1 invoices only
        client.force_authenticate(user=setup_data['admin_user'])
        response = client.get('/api/v1/invoices/')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == setup_data['invoice1'].id
        
        # Multi-org user should see invoices from their active organization
        client.force_authenticate(user=setup_data['multi_org_user'])
        
        # Default organization is org1
        response = client.get('/api/v1/invoices/')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == setup_data['invoice1'].id
        
        # Switch to org2 using header
        response = client.get(
            '/api/v1/invoices/',
            HTTP_X_ORGANIZATION_ID=str(setup_data['org2'].id)
        )
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == setup_data['invoice2'].id
    
    def test_create_invoice_permissions(self, setup_data):
        """Test that only users with proper permissions can create invoices."""
        client = APIClient()
        
        # New invoice data
        data = {
            'invoice_number': 'INV-003',
            'date': '2023-03-01',
            'due_date': '2023-03-31',
            'customer': 1,
            'status': 'draft',
            'items': [
                {
                    'description': 'Service A',
                    'quantity': 2,
                    'unit_price': 50.00
                }
            ]
        }
        
        # Admin should be able to create invoice
        client.force_authenticate(user=setup_data['admin_user'])
        response = client.post('/api/v1/invoices/', data, format='json')
        assert response.status_code == 201
        
        # Viewer should not be able to create invoice (no add_invoice permission)
        client.force_authenticate(user=setup_data['viewer_user'])
        response = client.post('/api/v1/invoices/', data, format='json')
        assert response.status_code == 403
    
    def test_special_actions_permission(self, setup_data):
        """Test that special actions respect custom permissions."""
        client = APIClient()
        invoice = setup_data['invoice1']
        
        # Accountant should be able to mark as paid (assuming they have permission)
        client.force_authenticate(user=setup_data['accountant_user'])
        
        # First change to sent status (needed for mark_as_paid action)
        invoice.status = 'sent'
        invoice.save()
        
        response = client.post(f'/api/v1/invoices/{invoice.id}/mark_as_paid/')
        
        # This will pass or fail depending on whether the accountant role 
        # has the mark_as_paid permission, which should be configured in fixtures
        # For this example, we'll assume they have it
        assert response.status_code == 200
        
        # Viewer should not be able to mark as paid
        client.force_authenticate(user=setup_data['viewer_user'])
        invoice.status = 'sent'  # Reset status
        invoice.save()
        
        response = client.post(f'/api/v1/invoices/{invoice.id}/mark_as_paid/')
        assert response.status_code == 403 