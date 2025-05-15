import calendar
from datetime import date, datetime,timedelta
import logging
from django.utils import timezone
from io import BytesIO
import json
import re
from django.http import BadHeaderError, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from openpyxl import Workbook
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from EMS import settings
from app.models import Attendance, Department, Performance, UserForDepartmentHead, Employee, Leave, Notification, Payroll, UserForEmployee
import pyqrcode
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.auth.models import User, Group

@login_required
def attendance(request):
    if request.user.groups.filter(name='HR').exists():
        employees = Employee.objects.filter(is_active=True)  
    else:
        try:
            department_head = UserForDepartmentHead.objects.get(user=request.user)
            department_instance = department_head.employee.department
            employees = Employee.objects.filter(is_active=True, department=department_instance)
        except UserForDepartmentHead.DoesNotExist:
            messages.error(request, 'You are not authorized to view this page.')
            return redirect('dashboard')

    date = datetime.now().date()
    return render(request, 'app/Attendance.html', {'employees': employees, 'date': date})

@login_required
def report(request):
    return render(request, 'app/work_hours_report.html')

@login_required
def profile(request):
    return render(request, 'app/Profile.html')

@login_required
def change_password(request):
    return render(request, 'app/change_pass.html')

from django.db import transaction, IntegrityError
# Employee CRUD
logger = logging.getLogger(__name__)

@login_required
def employee(request):
    departments = Department.objects.all()
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        gender = request.POST.get('gender')
        dob = request.POST.get('dob')
        address = request.POST.get('address')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        department_id = request.POST.get('department')
        position = request.POST.get('position')
        hire_date = request.POST.get('hire_date')
        salary = request.POST.get('salary')
        image = request.FILES.get('image')
        is_department_head = request.POST.get('is_department_head') == 'on'

        if not re.match("^[A-Za-z]+$", first_name):
            messages.error(request, 'First name should only contain letters.')
            return render(request, 'app/Add_employee.html', {'departments': departments})
        if not re.match("^[A-Za-z]+$", last_name):
            messages.error(request, 'Last name should only contain letters.')
            return render(request, 'app/Add_employee.html', {'departments': departments})

        department_instance = Department.objects.get(id=department_id)

        if Employee.objects.filter(first_name=first_name, last_name=last_name).exists():
            messages.error(request, 'An employee with this first name and last name already exists.')
            return render(request, 'app/Add_employee.html', {'departments': departments})
        if Employee.objects.filter(email=email).exists():
            messages.error(request, 'An employee with this email already exists.')
            return render(request, 'app/Add_employee.html', {'departments': departments})

        try:
            hire_date = datetime.strptime(hire_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid hire date format. Use YYYY-MM-DD.')
            return render(request, 'app/Add_employee.html', {'departments': departments})

        try:
            if is_department_head:
              
                if Employee.objects.filter(department=department_instance, is_department_head=True).exists():
                    messages.error(request, 'This department already has a head.')
                    return render(request, 'app/Add_employee.html', {'departments': departments})

                group = Group.objects.get(name='Manager')
            else:
                group = Group.objects.get(name='Employe')

            with transaction.atomic():
                employee = Employee.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    dob=dob,
                    address=address,
                    email=email,
                    phone=phone,
                    department=department_instance,
                    position=position,
                    hire_date=hire_date,
                    salary=salary,
                    image=image,
                    is_department_head=is_department_head
                )

                employee_info = {
                    "username": employee.email,
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "email": employee.email,
                    "phone": employee.phone,
                    "department": employee.department.department_name,
                    "position": employee.position,
                    "hire_date": hire_date.strftime('%Y-%m-%d')
                }
                employee_info_str = json.dumps(employee_info)
                qr_code = pyqrcode.create(employee_info_str)
                buffer = BytesIO()
                qr_code.png(buffer, scale=4)
                buffer.seek(0)
                employee.qr_code_image.save(f'{employee.pk}.png', ContentFile(buffer.read()))
                employee.save()

                
                if User.objects.filter(username=email).exists():
                    messages.error(request, 'A user with this email already exists.')
                    return render(request, 'app/Add_employee.html', {'departments': departments})
 
                if is_department_head:
                    user_for_department_head = UserForDepartmentHead(employee=employee)
                    user_for_department_head.save()
                    user_for_department_head.user.groups.add(group)
                else:
                    user_for_employee = UserForEmployee(employee=employee)
                    user_for_employee.save()
                    user_for_employee.user.groups.add(group)

            messages.success(request, 'Employee added successfully!')
            return render(request, 'app/Add_employee.html', {'success': True, 'departments': departments})

        except Group.DoesNotExist:
            messages.error(request, 'The required group does not exist. Please create it in the admin interface.')
            return render(request, 'app/Add_employee.html', {'departments': departments})
        except IntegrityError as e:
            logger.error(f'IntegrityError: {e}')
            messages.error(request, 'An error occurred while saving the employee. Please try again.')
            return render(request, 'app/Add_employee.html', {'departments': departments})
        except Exception as e:
            logger.error(f'Unexpected error: {e}')
            messages.error(request, 'An unexpected error occurred. Please try again.')
            return render(request, 'app/Add_employee.html', {'departments': departments})

    return render(request, 'app/Add_employee.html', {'departments': departments})

@login_required
def list_employees(request):
    search_query = request.GET.get('search', '').strip()
    
     
    if request.user.groups.filter(name='HR').exists():
        employees = Employee.objects.filter(is_active=True)
    else:
        try:
            department_head = UserForDepartmentHead.objects.get(user=request.user)
            department_instance = department_head.employee.department
        except UserForDepartmentHead.DoesNotExist:
            messages.error(request, 'You are not authorized to view this page.')
            return redirect('dashboard')

        employees = Employee.objects.filter(is_active=True, department=department_instance)

    if search_query:
        names = search_query.split()
        if len(names) == 2:
            first_name, last_name = names
            employees = employees.filter(first_name__icontains=first_name, last_name__icontains=last_name)
        else:
            employees = employees.filter(first_name__icontains=search_query) | employees.filter(last_name__icontains=search_query)

    return render(request, 'app/list_employees.html', {'employees': employees, 'search_query': search_query})

@login_required
def edit_employee(request, id):
    employee = get_object_or_404(Employee, id=id)
    departments = Department.objects.all()

    if request.method == 'POST':
        employee.first_name = request.POST.get('first_name')
        employee.last_name = request.POST.get('last_name')
        employee.gender = request.POST.get('gender')
        employee.dob = request.POST.get('dob')
        employee.address = request.POST.get('address')
        employee.email = request.POST.get('email')
        employee.phone = request.POST.get('phone')
        department_id = request.POST.get('department')
        employee.position = request.POST.get('position')
        employee.hire_date = request.POST.get('hire_date')
        employee.salary = request.POST.get('salary')

        if request.FILES.get('image'):
            employee.image = request.FILES.get('image')

        employee.department = get_object_or_404(Department, id=department_id)
        employee.save()

        return render(request, 'app/edit_employee.html', {'success': True,'employee': employee, 'departments': departments})

    return render(request, 'app/edit_employee.html', {'employee': employee, 'departments': departments})

@login_required
def delete_employee(request, id):
    employee = get_object_or_404(Employee, id=id)
    if request.method == 'POST':
        employee.is_active = False
        employee.save()
        messages.success(request, 'Employee deleted successfully.')
        return redirect('list_employees')
    return render(request, 'app/confirm_delete.html', {
        'object_name': f'{employee.first_name} {employee.last_name}',
        'delete_url': 'delete_employee',
        'delete_id': employee.id,
        'redirect_url': 'list_employees',
        'breadcrumb_name': 'Employee'
    })

@login_required
def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    return render(request, 'app/employee_detail.html', {'employee': employee})



#LEAVE CRUD
@login_required
def add_leave(request):
    is_hr = request.user.groups.filter(name='HR').exists()

    if is_hr:
        employees = Employee.objects.filter(is_active=True)
    else:
        try:
            department_head = UserForDepartmentHead.objects.get(user=request.user)
            department_instance = department_head.employee.department
            employees = Employee.objects.filter(is_active=True, department=department_instance)
        except UserForDepartmentHead.DoesNotExist:
            messages.error(request, 'You are not authorized to view this page.')
            return redirect('dashboard')

    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        leave_type = request.POST.get('leave_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        status = request.POST.get('status', 'Pending')

        employee = Employee.objects.get(id=employee_id)
        one_year_ago = datetime.now().date() - timedelta(days=365)
        if employee.hire_date > one_year_ago:
            messages.error(request, 'Only employees who have been employed for 1 year or more can apply for leave.')
            return render(request, 'app/add_leave.html', {'employees': employees})

        current_year = datetime.now().year
        leave_count = Leave.objects.filter(employee_id=employee_id, start_date__year=current_year).count()
        if leave_count >= 3:
            messages.error(request, 'Employees can apply for leave only 3 times per year.')
            return render(request, 'app/add_leave.html', {'employees': employees})

        if Leave.objects.filter(employee_id=employee_id, leave_type=leave_type, start_date=start_date).exists():
            messages.error(request, 'A leave with the same type and start date already exists for this employee.')
            return render(request, 'app/add_leave.html', {'employees': employees})

        leave_image = request.FILES.get('image', None)  
        try:
            leave = Leave.objects.create(
                employee_id=employee_id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                status=status,
                image=leave_image   
            )
            messages.success(request, 'Leave added successfully!')

            # In-App Notification
            hr_users = User.objects.filter(groups__name='HR')
            for hr_user in hr_users:
                Notification.objects.create(
                    user=hr_user,
                    message=f'Employee {employee.first_name} {employee.last_name} has applied for leave from {start_date} to {end_date}.',
                    leave=leave
                )
            return redirect('list_leave')

        except Exception as e:
            messages.error(request, 'An error occurred while adding leave. Please try again.')
            return render(request, 'app/add_leave.html', {'employees': employees})

    return render(request, 'app/add_leave.html', {'employees': employees})


@login_required
def edit_leave(request, id):
    leave = get_object_or_404(Leave, id=id)
    employees = Employee.objects.all()
    old_status = leave.status

    if request.method == 'POST':
        leave.employee_id = request.POST.get('employee')
        leave.leave_type = request.POST.get('leave_type')
        leave.start_date = datetime.strptime(request.POST.get('start_date'), '%m/%d/%Y').date()
        leave.end_date = datetime.strptime(request.POST.get('end_date'), '%m/%d/%Y').date()
        leave.status = request.POST.get('status')

        leave_image = request.FILES.get('image', None)
        if leave_image:   
            leave.image = leave_image

        try:
            leave.save()

            if old_status != leave.status:
                message = f'Hi {leave.employee.first_name},\n\nYour leave request from {leave.start_date} to {leave.end_date} has been: {leave.status}.\n\nRegards,\nHR Team'
                Notification.objects.create(
                    user=leave.employee.user,
                    message=message,
                    leave=leave
                )

            messages.success(request, 'Leave updated successfully!')
            return render(request, 'app/edit_leave.html', {'leave': leave, 'employees': employees, 'success': True})

        except Exception as e:
            messages.error(request, 'An error occurred while updating leave. Please try again.')
            return render(request, 'app/edit_leave.html', {'leave': leave, 'employees': employees})

    return render(request, 'app/edit_leave.html', {'leave': leave, 'employees': employees})

@login_required
def list_leave(request):
    query = request.GET.get('search')

    if request.user.groups.filter(name='HR').exists():
        leaves = Leave.objects.all()
    else:
        try:
            department_head = UserForDepartmentHead.objects.get(user=request.user)
            department_instance = department_head.employee.department
        except UserForDepartmentHead.DoesNotExist:
            messages.error(request, 'You are not authorized to view this page.')
            return redirect('dashboard')

        leaves = Leave.objects.filter(employee__department=department_instance)

    if query:
        leaves = leaves.filter(
            Q(employee__first_name__icontains=query) | 
            Q(employee__last_name__icontains=query)
        )
    
    return render(request, 'app/list_leave.html', {'leaves': leaves})

@login_required
def delete_leave(request, id):
    leave = get_object_or_404(Leave, id=id)
    if request.method == 'POST':
        leave.delete()
        return redirect('list_leave')
    return render(request, 'app/confirm_delete_leave.html', {'leave': leave})


#Department CRUD
@login_required
def list_departments(request):
    search_query = request.GET.get('search', '')
    departments = Department.objects.filter(is_active=True)
    
    if search_query:
        departments = departments.filter(department_name__icontains=search_query)

    return render(request, 'app/list_department.html', {'departments': departments})

@login_required
def add_department(request):
    if request.method == 'POST':
        department_name = request.POST.get('department_name')
        department_head_id = request.POST.get('department_head')
        description = request.POST.get('description')

        department_head = Employee.objects.get(id=department_head_id) if department_head_id else None

         
        if Department.objects.filter(department_name=department_name).exists():
            messages.error(request, 'A department with this name already exists.')
            return render(request, 'app/add_department.html', {'employees': Employee.objects.all()})
        
        Department.objects.create(
            department_name=department_name,
            department_head=department_head,
            description=description
        )

        messages.success(request, 'Department added successfully!')
        return render(request, 'app/add_department.html', {'success': True, 'employees': Employee.objects.all()})

    employees = Employee.objects.all()
    return render(request, 'app/add_department.html', {'employees': employees})

@login_required
def edit_department(request, id):
    department = get_object_or_404(Department, id=id)
    employees = Employee.objects.all()
    if request.method == 'POST':
        department.department_name = request.POST.get('department_name')
        department_head_id = request.POST.get('department_head')
        department.description = request.POST.get('description')
        department.department_head = Employee.objects.get(id=department_head_id) if department_head_id else None
        department.save()
        return render(request, 'app/edit_department.html', {'success': True})
    return render(request, 'app/edit_department.html', {'department': department, 'employees': employees})

@login_required
def delete_department(request, id):
    department = get_object_or_404(Department, id=id)
    if request.method == 'POST':
        department.is_active = False   
        department.save()
        messages.success(request, 'Department deleted successfully.')
        return redirect('list_departments')
    return render(request, 'app/confirm_delete.html', {
        'object_name': department.department_name,
        'delete_url': 'delete_department',
        'delete_id': department.id,
        'redirect_url': 'list_departments',
        'breadcrumb_name': 'Department'
    })


#Payroll
@login_required
def list_payrolls(request):
    if request.user.groups.filter(name='HR').exists():
        payrolls = Payroll.objects.all()  
    else:
        try:
            department_head = UserForDepartmentHead.objects.get(user=request.user)
            department_instance = department_head.employee.department
            payrolls = Payroll.objects.filter(employee__department=department_instance)
        except UserForDepartmentHead.DoesNotExist:
            messages.error(request, 'You are not authorized to view this page.')
            return redirect('dashboard')
    
    return render(request, 'app/list_payrolls.html', {'payrolls': payrolls})

@login_required
def payroll_invoice(request, id):
    payroll = get_object_or_404(Payroll, id=id)
    return render(request, 'app/payroll_invoice.html', {'payroll': payroll})


#Calculate Work hour
@login_required
def calculate_daily_hours(employee, date):
    try:
        attendance_record = Attendance.objects.get(employee=employee, date=date)
    except Attendance.DoesNotExist:
        return 0
    
    total_hours = timedelta()
    if attendance_record.check_in and attendance_record.check_out:
        total_hours += (attendance_record.check_out - attendance_record.check_in)

    return total_hours.total_seconds() / 3600.0

@login_required
def calculate_total_hours(employee, month, year):
    attendance_records = Attendance.objects.filter(employee=employee, date__year=year, date__month=month)

    total_hours = timedelta()
    for record in attendance_records:
        if record.check_in and record.check_out:
            total_hours += (record.check_out - record.check_in)

    return total_hours.total_seconds() / 3600.0

@login_required
def work_hours_report(request):
    search_query = request.GET.get('search', '').strip()

    try:
        department_head = UserForDepartmentHead.objects.get(user=request.user)
        department_instance = department_head.employee.department
    except UserForDepartmentHead.DoesNotExist:
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('dashboard')

    employees = Employee.objects.filter(is_active=True, department=department_instance)

    if search_query:
        names = search_query.split()
        if len(names) == 2:
            first_name, last_name = names
            employees = employees.filter(first_name__icontains=first_name, last_name__icontains=last_name)
        else:
            employees = employees.filter(first_name__icontains=search_query) | employees.filter(last_name__icontains=search_query)

    report = []
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())   
    end_of_week = start_of_week + timedelta(days=4)  

    dates = [start_of_week + timedelta(days=i) for i in range(5)] 

    for employee in employees:
        daily_hours = []
        total_hours = 0
        for date in dates:
            hours = calculate_daily_hours(employee, date)
            daily_hours.append(hours)
            total_hours += hours
        report.append({
            'employee': employee,
            'daily_hours': daily_hours,
            'total_hours': total_hours
        })

    return render(request, 'app/work_hours_report.html', {'report': report, 'dates': dates, 'search_query': search_query})


def calculate_hours(start, end):
    start_time = datetime.combine(datetime.min, start)
    end_time = datetime.combine(datetime.min, end)
    duration = end_time - start_time
    return duration.total_seconds() / 3600.0

@login_required
def monthly_work_hours_report(request):
    current_year = datetime.now().year
    months = range(1, 13)

    if request.method == 'POST':
        month = request.POST.get('month')
        year = request.POST.get('year')

        if not month or not year:
            return render(request, 'app/monthly_work_hours_form.html', {
                'error': 'Month and year are required',
                'current_year': current_year,
                'months': months
            })

        try:
            month = int(month)
            year = int(year)
        except ValueError:
            return render(request, 'app/monthly_work_hours_form.html', {
                'error': 'Invalid month or year format',
                'current_year': current_year,
                'months': months
            })

        if request.user.groups.filter(name='HR').exists():
            employees = Employee.objects.filter(is_active=True)
        else:
            try:
                department_head = UserForDepartmentHead.objects.get(user=request.user)
                department_instance = department_head.employee.department
                employees = Employee.objects.filter(is_active=True, department=department_instance)
            except UserForDepartmentHead.DoesNotExist:
                messages.error(request, 'You are not authorized to view this page.')
                return redirect('dashboard')

        report_data = []

        for employee in employees:
            employee_data = {
                'employee': employee,
                'days': [0] * calendar.monthrange(year, month)[1]
            }

            total_hours = 0
            for day in range(1, calendar.monthrange(year, month)[1] + 1):
                date = datetime(year, month, day).date()
                if date.weekday() < 5:
                    try:
                        attendance = Attendance.objects.get(employee=employee, date=date)
                        daily_hours = 0
                        if attendance.check_in and attendance.check_out:
                            daily_hours = (attendance.check_out - attendance.check_in).total_seconds() / 3600.0
                    except Attendance.DoesNotExist:
                        daily_hours = 0

                    total_hours += daily_hours
                    employee_data['days'][day - 1] = daily_hours

            employee_data['total_hours'] = total_hours
            report_data.append(employee_data)

        days_in_month = range(1, calendar.monthrange(year, month)[1] + 1)

        if 'download_excel' in request.POST:
            return download_excel(report_data, days_in_month, month, year)

        return render(request, 'app/monthly_work_hours_report.html', {
            'report_data': report_data,
            'month': month,
            'year': year,
            'days_in_month': days_in_month
        })

    return render(request, 'app/monthly_work_hours_form.html', {
        'current_year': current_year,
        'months': months
    })

def download_excel(report_data, days_in_month, month, year):
    output = BytesIO()
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = f"Report_{month}_{year}"

    headers = ["Employee"] + [str(day) for day in days_in_month] + ["Total Hours"]
    sheet.append(headers)

    for data in report_data:
        row = [f"{data['employee'].first_name} {data['employee'].last_name}"] + data['days'] + [data['total_hours']]
        sheet.append(row)

    workbook.save(output)
    output.seek(0)

    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=work_hours_report_{month}_{year}.xlsx'
    return response

#Dashboard
@login_required
def Dashboard(request):
    user = request.user
    department_head = get_object_or_404(UserForDepartmentHead, user=user)
    department = department_head.employee.department

   
    active_employees = Employee.objects.filter(is_active=True)
    total_employees = active_employees.count()
    total_dep = Department.objects.count()

   
    departments = Department.objects.all()
    employees_by_department = {department.department_name: active_employees.filter(department=department).count() for department in departments}

    today = date.today()
     
    new_hires = active_employees.filter(hire_date__year=today.year, hire_date__month=today.month).count()

    context = {
        'total_employees': total_employees,
        'employees_by_department': employees_by_department,
        'new_hires': new_hires,
        'total_dep': total_dep,
        'department_head': department_head,
        'department': department,
    }

    return render(request, 'app/dashboard.html', context)

@login_required
def edit_payroll(request, payroll_id):
    payroll = get_object_or_404(Payroll, id=payroll_id)
    
    if request.method == 'POST':
        payroll.pay_date = request.POST.get('pay_date')
        payroll.base_salary = request.POST.get('base_salary')
        payroll.bonuses = request.POST.get('bonuses')
        payroll.deductions = request.POST.get('deductions')
        payroll.taxes = request.POST.get('taxes')
        payroll.net_pay = request.POST.get('net_pay')
        
        payroll.save()
        messages.success(request, 'Payroll updated successfully!')
        return redirect('list_payrolls')

    return render(request, 'app/edit_payroll.html', {'payroll': payroll})

@csrf_exempt
def save_attendance(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        attendance_data = data.get('attendance_data', {})

        for employee_id, times in attendance_data.items():
            employee = Employee.objects.get(id=employee_id)
            date = times.get('date')
            morning_check_in = times.get('morning_check_in')
            morning_check_out = times.get('morning_check_out')
            afternoon_check_in = times.get('afternoon_check_in')
            afternoon_check_out = times.get('afternoon_check_out')

            attendance, created = Attendance.objects.get_or_create(employee=employee, date=date)
            if morning_check_in:
                attendance.morning_check_in = morning_check_in
            if morning_check_out:
                attendance.morning_check_out = morning_check_out
            if afternoon_check_in:
                attendance.afternoon_check_in = afternoon_check_in
            if afternoon_check_out:
                attendance.afternoon_check_out = afternoon_check_out
            attendance.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False})

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  
            messages.success(request, 'Your password has been successfully updated.')
            return redirect('dashboard')
    return render(request, 'app/change_password.html')

@login_required
@csrf_exempt
def qr_code_scan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            qr_data = json.loads(data['qr_data'])
            email = qr_data['email']

            employee = Employee.objects.get(email=email)
            today = timezone.now().date()

             
            attendance, created = Attendance.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={'check_in': timezone.now()}
            )
            if not created:
                if attendance.check_out is None:
                    attendance.check_out = timezone.now()
                    attendance.save()
                    return JsonResponse({'message': 'Checked out successfully'}, status=200)
                else:
                    return JsonResponse({'message': 'Already checked out for today'}, status=400)

            return JsonResponse({'message': 'Checked in successfully'}, status=200)
        except Employee.DoesNotExist:
            return JsonResponse({'message': 'Employee not found'}, status=404)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=400)
    return JsonResponse({'message': 'Invalid request method'}, status=405)

@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    context = {'notifications': notifications}
    return render(request, 'app/notifications.html', context)

@login_required
def some_view(request):
    unread_notifications_count = 0
    notifications = []
    is_hr = request.user.groups.filter(name='HR').exists()

    if is_hr:
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
        notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]   
    
    context = {
        'unread_notifications_count': unread_notifications_count,
        'notifications': notifications,
        'is_hr': is_hr,
        
    }
    return render(request, 'app/base.html', context) 


@login_required
def fetch_notifications(request):
    if request.user.groups.filter(name='HR').exists():
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        notifications = Notification.objects.filter(user=request.user, is_read=False).values('message', 'timestamp')[:5]  # Limit to the latest 5 notifications
        return JsonResponse({'unread_count': unread_count, 'notifications': list(notifications)})
    else:
        return JsonResponse({'unread_count': 0, 'notifications': []})
    
@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('dashboard')  

@login_required
@csrf_exempt
def qr_code_scanner(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            qr_data = data.get('qr_data')
            if not qr_data:
                return JsonResponse({'error': 'No QR data provided'}, status=400)

            employee_info = json.loads(qr_data)
            employee = Employee.objects.get(email=employee_info['email'])
        except (Employee.DoesNotExist, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid QR data'}, status=400)

        today = timezone.now().date()
        attendance, created = Attendance.objects.get_or_create(employee=employee, date=today)
        
        if not attendance.check_in:
            attendance.check_in = timezone.now()
            attendance.save()
            return JsonResponse({'message': 'Checked in successfully'})
        elif not attendance.check_out:
            attendance.check_out = timezone.now()
            attendance.save()
            return JsonResponse({'message': 'Checked out successfully'})
        else:
            return JsonResponse({'message': 'Already checked in and out today'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def manual_attendance(request):
    employees = Employee.objects.filter(is_active=True)
    
    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        
        employee = Employee.objects.get(id=employee_id)
        date = timezone.now().date()
        
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=date
        )
        
        if check_in:
            attendance.check_in = datetime.combine(date, datetime.strptime(check_in, '%H:%M').time())
        if check_out:
            attendance.check_out = datetime.combine(date, datetime.strptime(check_out, '%H:%M').time())
            
        attendance.save()
        messages.success(request, 'Attendance record added successfully!')
        return redirect('manual_attendance')

    context = {
        'employees': employees,
    }
    return render(request, 'app/manual_attendance.html', context)

@login_required
def attendance_list(request):
    attendance_records = Attendance.objects.all()

    context = {
        'attendance_records': attendance_records,
    }
    return render(request, 'app/attendance_list.html', context)

@login_required
def edit_attendance(request, attendance_id):
    attendance = get_object_or_404(Attendance, id=attendance_id)

    if request.method == 'POST':
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')

        if check_in:
            attendance.check_in = datetime.strptime(check_in, '%H:%M').time()
        if check_out:
            attendance.check_out = datetime.strptime(check_out, '%H:%M').time()

        attendance.save()
        messages.success(request, 'Attendance updated successfully!')
        return redirect('attendance_list')

    return render(request, 'app/edit_attendance.html', {'attendance': attendance})

@login_required
def evaluate_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

   
    current_month = datetime.now().month
    current_year = datetime.now().year

   
    if Performance.objects.filter(employee=employee, date__year=current_year, date__month=current_month).exists():
        messages.error(request, 'This employee has already been evaluated for this month.')
        return redirect('employee_detail', employee_id=employee_id)

    if request.method == 'POST':
      
        total_hours = calculate_total_hours(employee, current_month, current_year)

     
        comments = request.POST.get('comments')

        
        if total_hours == 0:
            
            if employee.user:
                try:
                    Notification.objects.create(
                        user=employee.user,
                        message=f'No evaluation submitted for {employee.first_name} {employee.last_name} due to no hours worked.',
                    )
                    messages.info(request, 'Notification sent to the employee about no hours worked.')
                except Exception as e:
                    messages.error(request, f"Failed to create notification for {employee.first_name}: {e}")
            messages.error(request, 'No hours worked this month. Evaluation cannot be completed.')
            return redirect('employee_detail', employee_id=employee_id)

       
        rating = calculate_rating_based_on_hours(total_hours)  

     
        Performance.objects.create(
            employee=employee,
            rating=rating,
            comments=comments,
            evaluated_by=request.user
        )

        messages.success(request, 'Performance evaluation submitted successfully!')
        return redirect('employee_detail', employee_id=employee_id)

    return render(request, 'app/evaluate_employee.html', {'employee': employee})

def calculate_rating_based_on_hours(total_hours):
    if total_hours >= 160:  
        return 5
    elif total_hours >= 120:
        return 4
    elif total_hours >= 80:
        return 3
    elif total_hours >= 40:
        return 2
    else:
        return 1  

from django.shortcuts import redirect, render
from django.contrib import messages
from app.models import Employee, Payroll, Notification
from app.management.commands.calculate_hours import calculate_total_hours
import decimal
from datetime import datetime, date

def generate_payroll(request):
    # Get the 'pay_date' from the request (coming from the form)
    pay_date_str = request.GET.get('pay_date')
    
    if pay_date_str:
        try:
            # Expecting 'YYYY-MM' format, and append '-01' to get a valid date
            pay_date = datetime.strptime(pay_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format. Use YYYY-MM.')
            return redirect('list_payrolls')  # Change this to the appropriate view
    else:
        # Default to current month if no input is provided
        pay_date = date.today()

    month = pay_date.month
    year = pay_date.year

    employees = Employee.objects.all()  # Fetch all employees
    notifications = []
    
    for employee in employees:
        # Check if a payroll for the same employee, month, and year already exists
        if Payroll.objects.filter(employee=employee, month=month, year=year).exists():
            messages.warning(request, f'Payroll for {employee.first_name} {employee.last_name} already exists for {month}/{year}. Skipping payroll generation for this employee.')
            continue  # Skip payroll creation for this employee and move to the next one
        
        # Calculate the total hours worked by the employee
        total_hours = decimal.Decimal(calculate_total_hours(employee, month, year))
        base_salary = employee.salary
        standard_hours = decimal.Decimal('160')
        hourly_rate = base_salary / standard_hours
        earned_salary = total_hours * hourly_rate
        threshold_hours = decimal.Decimal('160')
        deduction_per_hour = decimal.Decimal('10')
        
        # Calculate deductions if total hours are less than the standard threshold
        if total_hours < threshold_hours:
            additional_deductions = (threshold_hours - total_hours) * deduction_per_hour
        else:
            additional_deductions = decimal.Decimal('0')
        
        deductions = additional_deductions
        taxable_income = earned_salary - deductions
        taxes = taxable_income * decimal.Decimal('0.2')  # Example tax rate of 20%
        net_pay = earned_salary - deductions - taxes

        # Check if the employee worked any hours during the month
        if total_hours == 0:
            if employee.user:
                try:
                    Notification.objects.create(
                        user=employee.user,
                        message=f'No payroll received for {month}/{year} due to no hours worked.',
                    )
                    notifications.append(f'Notification created for {employee.first_name} {employee.last_name}')
                except Exception as e:
                    notifications.append(f"Failed to create notification for {employee.first_name} {employee.last_name}: {e}")
        else:
            # Create the payroll record for the employee
            payroll = Payroll(
                employee=employee,
                pay_date=pay_date,
                month=month,
                year=year,
                base_salary=earned_salary,
                bonuses=decimal.Decimal('0'),
                deductions=deductions,
                taxes=taxes,
                net_pay=net_pay
            )
            payroll.save()

            # Send a notification about payroll generation
            if employee.user:
                try:
                    Notification.objects.create(
                        user=employee.user,
                        message=f'Your payroll for {month}/{year} has been generated.',
                    )
                    notifications.append(f'Notification created for {employee.first_name} {employee.last_name}')
                except Exception as e:
                    notifications.append(f"Failed to create notification for {employee.first_name} {employee.last_name}: {e}")

    # Success message after processing all employees
    success_message = f'Successfully generated payroll for all employees on {pay_date_str}' if pay_date_str else f'Successfully generated payroll for all employees on {pay_date}'
    messages.success(request, success_message)
    
    return redirect('list_payrolls')


@login_required
def list_evaluations(request):
    search_query = request.GET.get('search', '').strip()

    if request.user.groups.filter(name='HR').exists():
        
        evaluations = Performance.objects.all()
    else:
        try:
            
            department_head = UserForDepartmentHead.objects.get(user=request.user)
            department_instance = department_head.employee.department
        except UserForDepartmentHead.DoesNotExist:
            messages.error(request, 'You are not authorized to view this page.')
            return redirect('dashboard')

        
        evaluations = Performance.objects.filter(employee__department=department_instance)

    
    if search_query:
        names = search_query.split()
        if len(names) == 2:
            first_name, last_name = names
            evaluations = evaluations.filter(employee__first_name__icontains=first_name, employee__last_name__icontains=last_name)
        else:
            evaluations = evaluations.filter(employee__first_name__icontains=search_query) | evaluations.filter(employee__last_name__icontains=search_query)

    return render(request, 'app/list_evaluations.html', {'evaluations': evaluations, 'search_query': search_query})
