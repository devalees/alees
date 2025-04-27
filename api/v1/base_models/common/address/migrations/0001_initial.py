from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Address",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when the record was created.",
                        verbose_name="Created At",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when the record was last updated.",
                        verbose_name="Updated At",
                    ),
                ),
                (
                    "street_address_1",
                    models.CharField(
                        help_text="Primary street address line.",
                        max_length=255,
                        verbose_name="Street Address 1",
                    ),
                ),
                (
                    "street_address_2",
                    models.CharField(
                        blank=True,
                        help_text="Secondary street address line (e.g., apartment, suite).",
                        max_length=255,
                        verbose_name="Street Address 2",
                    ),
                ),
                (
                    "city",
                    models.CharField(
                        db_index=True,
                        help_text="City or locality name.",
                        max_length=100,
                        verbose_name="City",
                    ),
                ),
                (
                    "state_province",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="State, province, or region name.",
                        max_length=100,
                        verbose_name="State/Province/Region",
                    ),
                ),
                (
                    "postal_code",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="Postal or ZIP code.",
                        max_length=20,
                        verbose_name="Postal/ZIP Code",
                    ),
                ),
                (
                    "country",
                    django_countries.fields.CountryField(
                        db_index=True,
                        help_text="ISO 3166-1 alpha-2 country code.",
                        max_length=2,
                        verbose_name="Country",
                    ),
                ),
                (
                    "latitude",
                    models.DecimalField(
                        blank=True,
                        decimal_places=7,
                        help_text="Geographic latitude coordinate.",
                        max_digits=10,
                        null=True,
                        verbose_name="Latitude",
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        blank=True,
                        decimal_places=7,
                        help_text="Geographic longitude coordinate.",
                        max_digits=10,
                        null=True,
                        verbose_name="Longitude",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        default="Active",
                        help_text="Current status of the address (e.g., Active, Inactive).",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "custom_fields",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional custom fields as JSON data.",
                        verbose_name="Custom Fields",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        help_text="User who created the record.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="auth.user",
                        verbose_name="Created By",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        help_text="User who last updated the record.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="auth.user",
                        verbose_name="Updated By",
                    ),
                ),
            ],
            options={
                "verbose_name": "Address",
                "verbose_name_plural": "Addresses",
                "indexes": [
                    models.Index(
                        fields=["country", "postal_code"],
                        name="api_v1_comm_country_c8c0f4_idx",
                    )
                ],
            },
        ),
    ]
