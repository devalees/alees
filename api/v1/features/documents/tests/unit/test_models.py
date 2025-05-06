import pytest
from django.db import models
from taggit.managers import TaggableManager
from django.contrib.contenttypes.fields import GenericForeignKey

from api.v1.features.documents.models import Document, DocumentStatus


class TestDocumentModel:
    """Test the Document model."""

    def test_document_fields(self):
        """Test that Document model has the expected fields."""
        # Get the model fields
        fields = {field.name: field for field in Document._meta.get_fields()}
        
        # Assert all expected fields are present
        assert 'title' in fields
        assert 'document_type' in fields
        assert 'status' in fields
        assert 'file' in fields
        assert 'version' in fields
        assert 'description' in fields
        assert 'tags' in fields
        assert 'custom_fields' in fields
        assert 'content_type' in fields
        assert 'object_id' in fields
        assert 'content_object' in fields
        assert 'organization' in fields  # From OrganizationScoped
        assert 'created_at' in fields  # From Timestamped
        assert 'updated_at' in fields  # From Timestamped
        assert 'created_by' in fields  # From Auditable
        assert 'updated_by' in fields  # From Auditable
        
        # Assert field types are correct
        assert isinstance(fields['title'], models.CharField)
        assert isinstance(fields['document_type'], models.ForeignKey)
        assert isinstance(fields['status'], models.CharField)
        assert isinstance(fields['file'], models.ForeignKey)
        assert isinstance(fields['version'], models.PositiveIntegerField)
        assert isinstance(fields['description'], models.TextField)
        assert isinstance(fields['tags'], TaggableManager)
        assert isinstance(fields['custom_fields'], models.JSONField)
        assert isinstance(fields['content_type'], models.ForeignKey)
        assert isinstance(fields['object_id'], models.CharField)
        assert isinstance(fields['content_object'], GenericForeignKey)
        assert isinstance(fields['organization'], models.ForeignKey)
        
    def test_document_meta(self):
        """Test Document model Meta options."""
        assert Document._meta.verbose_name == 'Document'
        assert Document._meta.verbose_name_plural == 'Documents'
        assert Document._meta.ordering == ['-created_at']
        
        # Verify custom permissions
        permissions = {perm[0]: perm[1] for perm in Document._meta.permissions}
        assert 'can_version_document' in permissions
        
    def test_document_status_choices(self):
        """Test Document status choices."""
        assert DocumentStatus.DRAFT == 'draft'
        assert DocumentStatus.ACTIVE == 'active'
        assert DocumentStatus.ARCHIVED == 'archived'
        assert DocumentStatus.PENDING_REVIEW == 'pending_review'
        
        # Verify all choices are defined
        assert len(DocumentStatus.CHOICES) == 4
        
    def test_str_representation(self):
        """Test the string representation of Document instances."""
        document = Document(title="Test Document", version=2)
        assert str(document) == 'Test Document (v2)' 