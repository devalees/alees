import django_filters
from django.db.models import Q

from api.v1.base_models.contact.models import Contact
from api.v1.base_models.contact.choices import ContactType, ContactStatus, ContactSource


class ContactFilter(django_filters.FilterSet):
    """Filter for Contact model."""
    search = django_filters.CharFilter(method='search_filter')
    contact_type = django_filters.ChoiceFilter(choices=ContactType.CHOICES)
    status = django_filters.ChoiceFilter(choices=ContactStatus.CHOICES)
    source = django_filters.ChoiceFilter(choices=ContactSource.CHOICES)
    has_organization = django_filters.BooleanFilter(
        field_name='linked_organization',
        lookup_expr='isnull',
        exclude=True
    )

    class Meta:
        model = Contact
        fields = ['contact_type', 'status', 'source', 'has_organization']

    def search_filter(self, queryset, name, value):
        """Search across multiple fields."""
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(organization_name__icontains=value) |
            Q(title__icontains=value)
        ) 