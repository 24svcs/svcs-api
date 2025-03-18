from django_filters.rest_framework import FilterSet
from org.models import Organization

class OrganizationFilter(FilterSet):
    class Meta:
        model = Organization
        fields = {
            'name': ['icontains'],
        }