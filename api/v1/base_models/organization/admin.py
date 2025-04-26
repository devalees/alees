from django.contrib import admin
from .models import OrganizationType

@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'updated_at', 'updated_by')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by') 