from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import OrganizationType, Organization, OrganizationMembership

@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'updated_at', 'updated_by')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')

@admin.register(Organization)
class OrganizationAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'name', 'code', 'organization_type', 'status', 'primary_contact', 'primary_address', 'currency')
    list_display_links = ('indented_title',)
    list_filter = ('status', 'organization_type', 'timezone', 'language')
    search_fields = ('name', 'code', 'organization_type__name')
    raw_id_fields = ('primary_contact', 'primary_address', 'currency', 'organization_type', 'parent')
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
    
    def indented_title(self, instance):
        return str(instance)
    indented_title.short_description = 'Organization'

@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'is_active', 'updated_at')
    list_filter = ('organization', 'role', 'is_active')
    search_fields = ('user__username', 'organization__name', 'role__name')
    list_select_related = ('user', 'organization', 'role')
    raw_id_fields = ('user', 'organization', 'role')  # Better for large numbers
    list_editable = ('is_active', 'role')
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by') 