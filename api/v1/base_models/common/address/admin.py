from django.contrib import admin
from .models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Admin configuration for the Address model."""

    list_display = (
        "id",
        "__str__",
        "city",
        "state_province",
        "postal_code",
        "country",
        "status",
        "updated_at",
    )
    search_fields = (
        "street_address_1",
        "street_address_2",
        "city",
        "state_province",
        "postal_code",
        "country",
    )
    list_filter = ("country", "status", "state_province")
    readonly_fields = ("created_at", "created_by", "updated_at", "updated_by")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "street_address_1",
                    "street_address_2",
                    "city",
                    "state_province",
                    "postal_code",
                    "country",
                )
            },
        ),
        (
            "Optional Info",
            {
                "classes": ("collapse",),
                "fields": ("latitude", "longitude", "status", "custom_fields"),
            },
        ),
        (
            "Audit Info",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "created_by", "updated_at", "updated_by"),
            },
        ),
    )
