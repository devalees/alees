# No need to register APIKey here as it's already registered by rest_framework_api_key
# The admin interface is available at /admin/rest_framework_api_key/apikey/

from django.contrib import admin
from .models import APIKey

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'prefix', 'created', 'expiry_date', 'revoked')
    list_filter = ('created', 'expiry_date', 'revoked')
    search_fields = ('name', 'prefix')
    ordering = ('-created',)
