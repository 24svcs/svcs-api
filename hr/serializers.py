from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone as tz
import pytz
from api.utils import validate_phone
from phonenumber_field.modelfields import PhoneNumberField
from api.utils.tz import convert_datetime_to_timezone
from hr.models import Department, Employee, Position, EmploymentDetails, Attendance
from django.db import transaction
from org.models import OrganizationPreferences
from django.core.cache import cache

class SimpleEmployeeSerializer(serializers.ModelSerializer):
    """Simplified serializer for Employee model, used for nested representations."""
    class Meta:
        model = Employee
        fields = ['id', 'first_name', 'last_name']


class DepartmentSerializer(serializers.ModelSerializer):
    manager = SimpleEmployeeSerializer(read_only=True)
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'image_url', 'manager']
        
        
class CreateDepartmentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'image_url', 'manager']
    
    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(_("Department name must be at least 2 characters long."))
            
        organization_id = self.context['organization_id']
        if Department.objects.select_related('organization').filter(organization_id=organization_id).filter(name__iexact=value).exists():
            raise serializers.ValidationError(_("A department with this name already exists in this organization."))
        return value
    
    
    def create(self, validated_data):
        organization_id = self.context['organization_id']
        return Department.objects.create(organization_id=organization_id, **validated_data)

class UpdateDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['name', 'description', 'manager', 'image_url']
    
    def validate_name(self, value):
        organization_id = self.context['organization_id']
        # Get queryset of departments with the same name in this company
        existing_departments = Department.objects.select_related('organization').filter(organization_id=organization_id).filter(name__iexact=value)
        
        # Exclude the current department being updated from the check
        if self.instance:
            existing_departments = existing_departments.exclude(id=self.instance.id)
            
        if existing_departments.exists():
            raise serializers.ValidationError(_("A department with this name already exists in this organization."))
        return value
    
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)   
    
    
    
# ================== Position serializers =========================

class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['id', 'title', 'description', 'department', 'salary_range_min', 'salary_range_max']
        
        
class CreatePositionSerializer(serializers.ModelSerializer):
    department_id = serializers.IntegerField()
    class Meta:
        model = Position
        fields = ['id', 'title', 'department_id', 'description', 'salary_range_min', 'salary_range_max']
    
    
    def validate_department_id(self, value):
        organization_id = self.context.get('organization_id')

        if not Department.objects.filter(id=value).exists():
            raise serializers.ValidationError(_("Department does not exist."))
        
        if organization_id and not Department.objects.filter(id=value, organization_id=organization_id).exists():
            raise serializers.ValidationError(_("Department does not belong to this organization."))
        
        return value
    
    def validate_title(self, value):
        organization_id = self.context.get('organization_id')

        if Position.objects.filter(department__organization_id=organization_id).filter(title__iexact=value).exists():
            raise serializers.ValidationError(_("A position with this title already exists in this department."))
        
        return value
    

    def create(self, validated_data):
        return Position.objects.create(**validated_data)


class UpdatePositionSerializer(serializers.ModelSerializer):
    department_id = serializers.IntegerField()
    class Meta:
        model = Position
        fields = ['title', 'description', 'department_id', 'salary_range_min', 'salary_range_max']
        
        
    def validate_department_id(self, value):
        if not Department.objects.filter(id=value).exists():
            raise serializers.ValidationError(_("Department does not exist."))
        
        # Ensure department belongs to the current company
        organization_id = self.context.get('organization_id')
        if organization_id and not Department.objects.filter(id=value, organization_id=organization_id).exists():
            raise serializers.ValidationError(_("Department does not belong to this organization."))

        return value
    

    
    def validate_title(self, value):
        organization_id = self.context['organization_id']
        # Get queryset of positions with the same title in this department
        existing_positions = Position.objects.filter(department__organization_id=organization_id).filter(title__iexact=value)
        
        # Exclude the current position being updated from the check
        if self.instance:
            existing_positions = existing_positions.exclude(id=self.instance.id)
            
        if existing_positions.exists():
            raise serializers.ValidationError(_("A position with this title already exists in this department."))
    
        
        return value
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)   
    
    
# ================== Employee serializers =========================

class EmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer for the Employee model with basic employee information.
    """
    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'gender', 'date_of_birth',
            'phone_number', 'address', 'emergency_contact_name', 'emergency_contact_phone',
            'created_at', 'updated_at'
        ]
    
    def to_representation(self, instance):
        """
        Convert datetime fields to the requested timezone
        """
        representation = super().to_representation(instance)
        
        # Get timezone from context (set by TimezoneMixin)
        timezone = self.context.get('timezone', pytz.UTC)
        
        # Convert datetime fields
        datetime_fields = ['created_at', 'updated_at']
        for field in datetime_fields:
            if representation.get(field):
                # Parse the datetime string
                dt = tz.datetime.fromisoformat(representation[field].replace('Z', '+00:00'))
                # Use the utility function for conversion
                converted_dt = convert_datetime_to_timezone(dt, timezone)
                # Format back to ISO 8601
                representation[field] = converted_dt.isoformat()
        
        return representation


class EmploymentDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for the EmploymentDetails model with employment-related information.
    """
    class Meta:
        model = EmploymentDetails
        fields = [
            'position', 'hire_date', 'employment_status', 'salary',
            'shift_start', 'shift_end', 'days_off', 'annual_leave_days',
            'sick_leave_days', 'created_at', 'updated_at'
        ]
        
    def validate_days_off(self, value):
        """Validate that days off are valid day names."""
        if value:
            valid_days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
            for day in value:
                if day not in valid_days:
                    raise serializers.ValidationError(_(f"Invalid day '{day}'. Must be one of: {', '.join(valid_days)}"))
        return value
        
    def to_representation(self, instance):
        """
        Convert datetime fields to the requested timezone
        """
        representation = super().to_representation(instance)
        
        # Get timezone from context (set by TimezoneMixin)
        timezone = self.context.get('timezone', pytz.UTC)
        
        # Convert datetime fields
        datetime_fields = ['created_at', 'updated_at']
        for field in datetime_fields:
            if representation.get(field):
                # Parse the datetime string
                dt = tz.datetime.fromisoformat(representation[field].replace('Z', '+00:00'))
                # Use the utility function for conversion
                converted_dt = convert_datetime_to_timezone(dt, timezone)
                # Format back to ISO 8601
                representation[field] = converted_dt.isoformat()
        
        return representation


class EmployeeWithDetailsSerializer(EmployeeSerializer):
    """
    Combined serializer that includes both Employee and EmploymentDetails information.
    """
    employment_details = EmploymentDetailsSerializer(read_only=True)
    
    class Meta(EmployeeSerializer.Meta):
        fields = EmployeeSerializer.Meta.fields + ['employment_details']


class CreateEmployeeSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField(validators=[validate_phone.validate_phone])
    id = serializers.UUIDField(read_only=True)
    
    # Employment details fields
    position_id = serializers.IntegerField(write_only=True)
    hire_date = serializers.DateField(write_only=True)
    employment_status = serializers.ChoiceField(choices=EmploymentDetails.EMPLOYMENT_STATUS, default='FT', write_only=True)
    salary = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True, required=False, write_only=True)
    shift_start = serializers.TimeField(required=False, allow_null=True, write_only=True)
    shift_end = serializers.TimeField(required=False, allow_null=True, write_only=True)
    days_off = serializers.JSONField(required=False, allow_null=True, write_only=True)
    annual_leave_days = serializers.IntegerField(default=0, required=False, write_only=True)
    sick_leave_days = serializers.IntegerField(default=0, required=False, write_only=True)
    
    
    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'gender', 'date_of_birth', 
            'phone_number', 'address', 'emergency_contact_name', 'emergency_contact_phone',
            # Employment details fields
            'position_id', 'hire_date', 'employment_status', 'salary',
            'shift_start', 'shift_end', 'days_off', 'annual_leave_days', 'sick_leave_days'
        ]
  
    def validate_position_id(self, value):
        organization_id = self.context['organization_id']
        # Check if the position belongs to a department in the current company
        if not Position.objects.select_related('department').filter(
            id=value,
            department__organization_id=organization_id
        ).exists():
            raise serializers.ValidationError(_("This position does not belong to a department in this organization."))
        return value
    
    def validate_gender(self, value):
        if value not in [choice[0] for choice in Employee.GENDER_CHOICES]:
            raise serializers.ValidationError(_("Invalid gender."))
        return value
    
    def validate_hire_date(self, value):
        if value > tz.now().date():
            raise serializers.ValidationError(_("Hire date cannot be in the future."))
        return value
    
    def validate_employment_status(self, value):
        if value not in [choice[0] for choice in EmploymentDetails.EMPLOYMENT_STATUS]:
            raise serializers.ValidationError(_("Invalid employment status."))
        return value
    
    def validate_date_of_birth(self, value):
        today = tz.now().date()
        if value > today:
            raise serializers.ValidationError(_("Date of birth cannot be in the future."))
        
        # Check if employee is at least 16 years old
        min_age_date = today.replace(year=today.year - 16)
        if value > min_age_date:
            raise serializers.ValidationError(_("Employee must be at least 16 years old."))
        
        return value
    
    def validate_salary(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(_("Salary cannot be negative."))
        return value
    
    def validate_days_off(self, value):
        if value:
            valid_days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
            for day in value:
                if day not in valid_days:
                    raise serializers.ValidationError(_(f"Invalid day '{day}'. Must be one of: {', '.join(valid_days)}"))
        return value
    
    def validate(self, data):
        # Validate shift times if both are provided
        if data.get('shift_start') and data.get('shift_end'):
            if data['shift_start'] >= data['shift_end']:
                raise serializers.ValidationError(_("Shift end time must be after shift start time."))
        
        return data
    
    def create(self, validated_data):
        organization_id = self.context['organization_id']
        
        # Extract employment details data
        employment_details_fields = [
            'position_id', 'hire_date', 'employment_status', 'salary',
            'shift_start', 'shift_end', 'days_off', 'annual_leave_days', 'sick_leave_days'
        ]
        
        employment_details_data = {}
        for field in employment_details_fields:
            if field in validated_data:
                employment_details_data[field] = validated_data.pop(field)
        
        # Get position object from position_id
        if 'position_id' in employment_details_data:
            position_id = employment_details_data.pop('position_id')
            try:
                position = Position.objects.get(id=position_id)
                employment_details_data['position'] = position
            except Position.DoesNotExist:
                raise serializers.ValidationError(_("Position does not exist."))
                
        with transaction.atomic():
            # Create employee
            employee = Employee.objects.create(organization_id=organization_id, **validated_data)
            
            # Create employment details
            EmploymentDetails.objects.create(employee=employee, **employment_details_data)
        
        return employee
    
    def to_representation(self, instance):
        # After creating, return the full employee data with employment details
        serializer = EmployeeWithDetailsSerializer(instance, context=self.context)
        return serializer.data


class UpdateEmployeeSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField(validators=[validate_phone.validate_phone]) 
    id = serializers.UUIDField(read_only=True)
    
    class Meta:
        model = Employee
        fields = ['id', 'first_name', 'last_name', 'gender', 'date_of_birth', 
                 'phone_number', 'address', 'emergency_contact_name', 'emergency_contact_phone']
    
    def validate_gender(self, value):
        if value not in [choice[0] for choice in Employee.GENDER_CHOICES]:
            raise serializers.ValidationError(_("Invalid gender."))
        return value
    
    def validate_date_of_birth(self, value):
        today = tz.now().date()
        if value > today:
            raise serializers.ValidationError(_("Date of birth cannot be in the future."))
        
        # Check if employee is at least 16 years old    
        min_age_date = today.replace(year=today.year - 16)
        if value > min_age_date:
            raise serializers.ValidationError(_("Employee must be at least 16 years old."))
        return value
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class UpdateEmploymentDetailsSerializer(serializers.ModelSerializer):
    position_id = serializers.IntegerField()

    
    class Meta:
        model = EmploymentDetails
        fields = [
            'position_id', 'hire_date', 'employment_status', 'salary',
            'shift_start', 'shift_end', 'days_off', 'annual_leave_days', 'sick_leave_days'
        ]
    
    def validate_position_id(self, value):
        organization_id = self.context['organization_id']
        # Check if the position belongs to a department in the current company
        if not Position.objects.filter(
            id=value,
            department__organization_id=organization_id
        ).exists():
            raise serializers.ValidationError(_("This position does not belong to a department in this organization."))
        return value
    
    def validate_hire_date(self, value):
        if value > tz.now().date():
            raise serializers.ValidationError(_("Hire date cannot be in the future."))
        return value
    
    def validate_employment_status(self, value):
        if value not in [choice[0] for choice in EmploymentDetails.EMPLOYMENT_STATUS]:
            raise serializers.ValidationError(_("Invalid employment status."))
        return value
    
    def validate_salary(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(_("Salary cannot be negative."))
        return value
    
    def validate_days_off(self, value):
        if value:
            valid_days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
            for day in value:
                if day not in valid_days:
                    raise serializers.ValidationError(_(f"Invalid day '{day}'. Must be one of: {', '.join(valid_days)}"))
        return value
    
    def validate(self, data):
        # Validate shift times if both are provided
        if data.get('shift_start') and data.get('shift_end'):
            if data['shift_start'] >= data['shift_end']:
                raise serializers.ValidationError(_("Shift end time must be after shift start time."))
        
        return data
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
        
        
# ================== Attendance serializers =========================

class AttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer for the Attendance model with employee attendance information.
    """
    employee_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendance
        fields = ['id', 'employee', 'employee_name', 'date', 'time_in', 'time_out', 'status', 'note']
    
    def get_employee_name(self, obj):
        """Get the full name of the employee."""
        return f"{obj.employee.first_name} {obj.employee.last_name}"


class CheckInOutSerializer(serializers.Serializer):
    """
    Serializer for handling employee check-in and check-out operations.
    This serializer handles both creating new attendance records (check-in)
    and updating existing records (check-out).
    """
    employee_id = serializers.CharField()
    note = serializers.CharField(required=False, allow_blank=True, default='')
    
    def validate_employee_id(self, value):
        """Validate that the employee exists and belongs to the organization."""
        organization_id = self.context.get('organization_id')
        
        try:
            Employee.objects.get(id=value, organization_id=organization_id)
        except Employee.DoesNotExist:
            raise serializers.ValidationError(_("Employee not found in this organization."))
        
        return value
    
    def _get_organization_timezone(self, organization_id):
        """
        Helper method to get the organization's timezone.
        Uses caching to reduce database queries.
        """
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
    
    def _get_current_datetime(self, organization_id):
        """
        Helper method to get the current date and time in the organization's timezone.
        """
        organization_timezone = self._get_organization_timezone(organization_id)
        
        current_datetime = tz.now()
        if organization_timezone != pytz.UTC:
            current_datetime = current_datetime.astimezone(organization_timezone)
        
        return current_datetime
    
    def _handle_check_in(self, employee_id, current_date, current_time, note, organization_id):
        """
        Helper method to handle employee check-in.
        Creates a new attendance record with appropriate status.
        """
        employee = Employee.objects.get(id=employee_id)
        
        # Get employment details to determine status
        try:
            employment_details = EmploymentDetails.objects.get(employee_id=employee_id)
            
            # Determine status based on shift start time
            status = 'present'
            if employment_details.shift_start:
                # Add a 15-minute grace period for lateness determination
                # An employee is considered late if they check in more than 15 minutes
                # after their scheduled shift start time
                from datetime import datetime, timedelta
                
                # Convert shift_start to datetime for easier manipulation
                shift_start_dt = datetime.combine(current_date, employment_details.shift_start)
                late_threshold_dt = shift_start_dt + timedelta(minutes=15)
                
                # Extract time component
                late_threshold = late_threshold_dt.time()
                
                # Check if employee is late (beyond grace period)
                if current_time > late_threshold:
                    status = 'late'
                
        except EmploymentDetails.DoesNotExist:
            # If no employment details, default to present
            status = 'present'
        
        # Create new attendance record
        attendance = Attendance.objects.create(
            employee=employee,
            date=current_date,
            time_in=current_time,
            status=status,
            note=note,
            organization_id=organization_id
        )
        
        return attendance
    
    def _handle_check_out(self, attendance, current_time, note, employee_id):
        """
        Helper method to handle employee check-out.
        Updates the existing attendance record with check-out time.
        """
        # Get employment details to check shift end time
        try:
            employment_details = EmploymentDetails.objects.get(employee_id=employee_id)
            
            # If employee is trying to check out before their shift end time
            if employment_details.shift_end and current_time < employment_details.shift_end:
                # Prevent early checkout - only admins can do this
                raise serializers.ValidationError(_(
                    "You cannot check out before your scheduled end time. Please contact an administrator."
                ))
                
            # Calculate work duration to update status if needed
            from datetime import datetime, date, timedelta
            
            # Create datetime objects for comparison
            dummy_date = date(2000, 1, 1)  # Use any date
            dt_in = datetime.combine(dummy_date, attendance.time_in)
            dt_out = datetime.combine(dummy_date, current_time)
            
            # If time_out is earlier than time_in (overnight shift), add a day to time_out
            if dt_out < dt_in:
                dt_out = datetime.combine(dummy_date + timedelta(days=1), current_time)
            
            # Calculate duration in hours
            duration = (dt_out - dt_in).total_seconds() / 3600
            
            # If worked less than 4 hours, mark as half day
            # if duration < 4:
            #     attendance.status = 'half_day'
                
        except EmploymentDetails.DoesNotExist:
            # If no employment details, allow checkout
            pass
        
        # Update time_out
        attendance.time_out = current_time
        
        # Update note if provided
        if note:
            attendance.note = note
            
        attendance.save()
        return attendance
    
    def save(self):
        """
        Save method that handles both check-in and check-out operations.
        """
        employee_id = self.validated_data.get('employee_id')
        note = self.validated_data.get('note', '')
        organization_id = self.context.get('organization_id')
        
        # Get current date and time in the organization's timezone
        current_datetime = self._get_current_datetime(organization_id)
        current_date = current_datetime.date()
        current_time = current_datetime.time()
        
        # Check if attendance record exists for today
        try:
            attendance = Attendance.objects.get(employee_id=employee_id, date=current_date)
            
            # If time_out is already set, employee has already checked out
            if attendance.time_out is not None:
                raise serializers.ValidationError(_("Employee has already checked out today."))
            
            # Handle check-out
            return self._handle_check_out(attendance, current_time, note, employee_id)
            
        except Attendance.DoesNotExist:
            # No attendance record exists, handle check-in
            return self._handle_check_in(employee_id, current_date, current_time, note, organization_id)


class AdminAttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer for administrators to manage attendance records.
    Allows full control over all attendance fields.
    """
    class Meta:
        model = Attendance
        fields = ['id', 'employee', 'date', 'time_in', 'time_out', 'status', 'note']
    
    def validate(self, data):
        """Validate attendance data, ensuring time_out is after time_in."""
        # Ensure time_out is after time_in if both are provided
        if data.get('time_out') and data.get('time_in') and data['time_out'] <= data['time_in']:
            raise serializers.ValidationError(_("Check-out time must be after check-in time."))
        
        # If status is being updated to 'half_day', validate work duration
        if data.get('status') == 'half_day' and data.get('time_in') and data.get('time_out'):
            from datetime import datetime, date
            
            # Create datetime objects for comparison
            dummy_date = date(2000, 1, 1)
            dt_in = datetime.combine(dummy_date, data['time_in'])
            dt_out = datetime.combine(dummy_date, data['time_out'])
            
            # Calculate duration in hours
            duration = (dt_out - dt_in).total_seconds() / 3600
            
            # Warn if half_day status doesn't match duration
            if duration >= 4:
                self.context['warnings'] = [
                    _("Work duration is 4 hours or more, but status is set to 'half_day'.")
                ]
        
        return data
        
        
