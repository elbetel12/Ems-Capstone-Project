from django import forms
from django.contrib import admin
from django.utils.html import mark_safe

from .models import Department, UserForDepartmentHead, Employee, Attendance, Leave, Payroll, UserForEmployee,Performance

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'check_in', 'check_out']
        widgets = {
            'check_in': forms.DateTimeInput(format='%Y-%m-%d %H:%M:%S', attrs={'type': 'datetime-local'}),
            'check_out': forms.DateTimeInput(format='%Y-%m-%d %H:%M:%S', attrs={'type': 'datetime-local'}),
        }

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    form = AttendanceForm
    list_display = ['employee', 'date', 'check_in', 'check_out']
    list_filter = ['date', 'employee']
    search_fields = ['employee__first_name', 'employee__last_name']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['department_name', 'department_head', 'is_active']
    list_filter = ['department_name', 'is_active']
    search_fields = ['department_name']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'position', 'department', 'hire_date', 'salary', 'is_department_head', 'image_tag', 'is_active']
    list_filter = ['position', 'department', 'hire_date', 'is_active']
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['image_tag']

    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" />')
        return "No Image"
    image_tag.short_description = 'Image'

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status', 'image_tag']
    list_filter = ['leave_type', 'status']
    search_fields = ['employee__first_name', 'employee__last_name']
    readonly_fields = ['image_tag']

    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" />')
        return "No Image"
    image_tag.short_description = 'Image'

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ['employee', 'pay_date', 'month', 'year', 'base_salary', 'bonuses', 'deductions', 'taxes', 'net_pay']
    list_filter = ['pay_date', 'month', 'year']
    search_fields = ['employee__first_name', 'employee__last_name']


@admin.register(UserForDepartmentHead)
class DepartmentHeadAdmin(admin.ModelAdmin):
    list_display = ['employee', 'user']
    search_fields = ['employee__first_name', 'employee__last_name', 'user__username']

class UserForEmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee', 'user')
    search_fields = ('employee__first_name', 'employee__last_name', 'user__username')

admin.site.register(UserForEmployee, UserForEmployeeAdmin)


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'rating', 'evaluated_by')
    list_filter = ('date', 'rating', 'employee')
    search_fields = ('employee__first_name', 'employee__last_name', 'comments')

    def get_employee_full_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"
    get_employee_full_name.short_description = 'Employee'

    def get_evaluated_by_full_name(self, obj):
        return f"{obj.evaluated_by.first_name} {obj.evaluated_by.last_name}"
    get_evaluated_by_full_name.short_description = 'Evaluated By'