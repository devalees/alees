from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

# Consider django-json-widget for better JSON display
# from jsoneditor.forms import JSONEditor
# from django.db import models

from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user_display', 'organization_display', 'action_type', 'object_link', 'short_object_repr')
    list_filter = ('action_type', ('created_at', admin.DateFieldListFilter), 'organization', 'user', 'content_type')
    search_fields = ('user__username', 'organization__name', 'object_repr', 'object_id', 'changes', 'context')
    list_select_related = ('user', 'organization', 'content_type')
    # Make all fields read-only by default
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    # Increase pagination count for better overview
    list_per_page = 50

    # Optional: Use django-json-widget for better JSON fields if installed
    # formfield_overrides = {
    #     models.JSONField: {'widget': JSONEditor},
    # }

    def has_add_permission(self, request):
        """Audit logs should not be manually added."""
        return False

    def has_change_permission(self, request, obj=None):
        """Audit logs are immutable."""
        return False # Typically read-only, maybe allow superuser?

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion through admin (use purging strategy instead)."""
        return False

    @admin.display(description='User', ordering='user__username')
    def user_display(self, obj):
        return obj.user or 'System'

    @admin.display(description='Organization', ordering='organization__name')
    def organization_display(self, obj):
        return obj.organization or '-'

    @admin.display(description='Object', ordering='content_type,object_id')
    def object_link(self, obj):
        """Create link to the related object's admin change page if possible."""
        if obj.content_object:
            try:
                # Construct the admin URL name
                opts = obj.content_type.model_class()._meta
                admin_url_name = f"admin:{opts.app_label}_{opts.model_name}_change"
                admin_url = reverse(admin_url_name, args=[obj.object_id])
                # Display a truncated representation as the link text
                display_text = obj.short_object_repr(self, obj)
                return format_html('<a href="{}">{}</a>', admin_url, display_text)
            except Exception: # Handle cases where reverse fails or model not in admin
                return obj.short_object_repr(self, obj) # Fallback to short repr
        return '-' # No content object linked

    @admin.display(description='Details', ordering='object_repr')
    def short_object_repr(self, obj):
        """Display a truncated object representation."""
        if obj.object_repr:
            return (obj.object_repr[:75] + '...') if len(obj.object_repr) > 75 else obj.object_repr
        elif obj.object_id:
            return f"<{obj.content_type.name} ID: {obj.object_id}>"
        return 'System Event'

    # Override the default object_repr column with the shorter version
    short_object_repr.short_description = "Object Details"
