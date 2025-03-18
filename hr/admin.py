from django.contrib import admin

from .models import Department, Position, Employee, EmploymentDetails, Attendance


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'organization', 'manager']
    search_fields = ['name', 'organization__name']
    list_filter = ['organization']
    

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'department', 'salary_range_min', 'salary_range_max']
    search_fields = ['title', 'department__name']
    list_filter = ['department']
    
    

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'phone_number']

    
    
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'employee', 'time_in', 'time_out', 'organization']
    search_fields = ['employee__first_name', 'employee__last_name', 'organization__name']
    list_filter = ['organization']
