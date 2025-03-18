from django_filters.rest_framework import FilterSet
from hr.models import Attendance

class AttendanceFilter(FilterSet):


    class Meta:
        model = Attendance
        fields = {
            'status': ['exact'],
            'employee__first_name': ['icontains'],
            'employee__last_name': ['icontains'],
            'date': ['gte', 'lte']
        }