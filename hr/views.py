from rest_framework.viewsets import ModelViewSet
from hr.serializers import(
     DepartmentSerializer, CreateDepartmentSerializer, Department,  UpdateDepartmentSerializer, CreatePositionSerializer, UpdatePositionSerializer, PositionSerializer, Position, CreateEmployeeSerializer, UpdateEmployeeSerializer, EmployeeSerializer, Employee

)
from api.mixins import TimezoneMixin
from core.models import Permission
from django.utils.translation import gettext as _
from rest_framework.exceptions import PermissionDenied
from hr.serializers import CheckInOutSerializer, Attendance, AttendanceSerializer
from rest_framework.response import Response
from rest_framework import status
from hr.models import EmploymentDetails
from datetime import datetime, date, timedelta
from org.models import OrganizationPreferences
import pytz
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from hr.filters import AttendanceFilter
from api.pagination import CustomPagination


class DepartmentModelViewset(ModelViewSet):
    def get_queryset(self):
        return Department.objects.filter(organization_id=self.kwargs['organization_pk'])
    
    def get_serializer_class(self):
        if self.request.method in 'POST':
            return  CreateDepartmentSerializer
        elif self.request.method in ['PUT', 'PATCH']:
            return UpdateDepartmentSerializer
        return DepartmentSerializer
    
    def get_serializer_context(self):
        return {'organization_id': self.kwargs['organization_pk']}
    
    
    # def get_permissions(self):
    #     if self.request.method in ['HEAD', 'OPTIONS']:
    #         return [IsAuthenticated()]
    #     if  self.request.method in 'POST':
    #         return [IsAuthenticated(), OrganizationPermission(Permission.CREATE_ORGANIZATION_DEPARTMENT)]
    #     elif self.request.method in ['PUT', 'PATCH']:
    #         return [IsAuthenticated(), OrganizationPermission(Permission.EDIT_ORGANIZATION_DEPARTMENT)]
    #     elif self.request.method in 'DELETE':
    #         return [IsAuthenticated(), OrganizationPermission(Permission.DELETE_ORGANIZATION_DEPARTMENT)]
    #     return [IsAuthenticated(), OrganizationPermission(Permission.VIEW_ORGANIZATION_DEPARTMENT)]
    
    
    
    #Todo Working Solution
    # def perform_create(self, serializer):
    #     # Check if the user has the proper permission
    #     organization_id = self.kwargs['organization_pk']
        
    #     # Get the organization member for this user
    #     member = self.request.user.memberships.filter(
    #         organization_id=organization_id,
    #         status='ACTIVE'
    #     ).first()
        
    #     if not member or not member.permissions.filter(name=Permission.CREATE_ORGANIZATION_DEPARTMENT).exists():
    #         raise PermissionDenied(_("You don't have permission to create departments."))
        
        
        
        serializer.save()
class PositionModelViewset(ModelViewSet):
    def get_queryset(self):
        return Position.objects.select_related('department').filter(department__organization_id=self.kwargs['organization_pk'])
    
    def get_serializer_class(self):
        if self.request.method in 'POST':
            return CreatePositionSerializer
        elif self.request.method in ['PUT', 'PATCH']:
            return UpdatePositionSerializer
        return PositionSerializer
    
    def get_serializer_context(self):
        return {'organization_id': self.kwargs['organization_pk']}
    
    
    
    
class EmployeeModelViewset(TimezoneMixin, ModelViewSet):
    def get_queryset(self):
        return Employee.objects.filter(organization_id=self.kwargs['organization_pk'])
    
    def get_serializer_class(self):
        if self.request.method in 'POST':
            return CreateEmployeeSerializer
        elif self.request.method in ['PUT', 'PATCH']:
            return UpdateEmployeeSerializer
        return EmployeeSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization_id'] = self.kwargs['organization_pk']
        return context
    
    

class AttendanceModelViewset(TimezoneMixin, ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_class = AttendanceFilter
    pagination_class = CustomPagination
    def get_queryset(self):
        queryset = Attendance.objects.filter(organization_id=self.kwargs['organization_pk'])
        
        # By default, filter to show only current date's attendance records
        if not self.request.query_params.get('date__gte') and not self.request.query_params.get('date__lte'):
            # Get organization timezone
            organization_timezone = self.get_organization_timezone()

            
            # Get current datetime in organization's timezone
            current_datetime = datetime.now(organization_timezone)
            today = current_datetime.date()
            
            queryset = queryset.filter(date=today)
        
        return queryset
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CheckInOutSerializer
        return AttendanceSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization_id'] = self.kwargs['organization_pk']
        return context
    
    def get_organization_timezone(self):
        """
        Get the organization's timezone from preferences.
        Uses caching to reduce database queries.
        """
        organization_id = self.kwargs['organization_pk']
        cache_key = f"org_timezone_{organization_id}"
        cached_timezone = cache.get(cache_key)
        
        if cached_timezone:
            return cached_timezone
        
        try:
            org_preferences = OrganizationPreferences.objects.select_related('organization').get(
                organization_id=organization_id
            )
            organization_timezone = org_preferences.timezone
            
            # Cache the timezone for 1 hour (3600 seconds)
            cache.set(cache_key, organization_timezone, 3600)
            
            return organization_timezone
        except OrganizationPreferences.DoesNotExist:
            # Default to UTC if preferences not found
            return pytz.UTC
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attendance = serializer.save()
        
        # Get employee information
        employee = attendance.employee
        
        # Get position information if available
        position_title = None
        try:
            employment_details = EmploymentDetails.objects.select_related('position').get(employee=employee)
            if employment_details.position:
                position_title = employment_details.position.title
        except:
            pass
        
        # Calculate work duration if checked out
        work_duration = None
        if attendance.time_out:
            dummy_date = date(2000, 1, 1)
            dt_in = datetime.combine(dummy_date, attendance.time_in)
            dt_out = datetime.combine(dummy_date, attendance.time_out)
            
            if dt_out < dt_in:
                dt_out = datetime.combine(dummy_date + timedelta(days=1), attendance.time_out)
            
            duration_seconds = (dt_out - dt_in).total_seconds()
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            work_duration = f"{hours}h {minutes}m"
        
        # Get the organization's timezone from preferences
        organization_timezone = self.get_organization_timezone()
        
        # Format times in the organization's timezone
        from django.utils import timezone as tz
        
        # Format the response
        response_data = {
            'id': str(attendance.id),
            'employee': {
                'id': str(employee.id),
                'name': f"{employee.first_name} {employee.last_name}",
                'position': position_title,
            },
            'attendance': {
                'date': attendance.date.strftime('%Y-%m-%d'),
                'time_in': attendance.time_in.strftime('%H:%M:%S'),
                'time_out': attendance.time_out.strftime('%H:%M:%S') if attendance.time_out else None,
                'status': attendance.status,
                'status_display': attendance.get_status_display() if hasattr(attendance, 'get_status_display') else attendance.status,
                'work_duration': work_duration,
                'note': attendance.note,
                'timezone': str(organization_timezone),  # Include timezone info in response
            },
            'action': 'check_out' if attendance.time_out else 'check_in',
            'message': _("Successfully checked out.") if attendance.time_out else _("Successfully checked in.")
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)