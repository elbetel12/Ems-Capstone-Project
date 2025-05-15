# views.py
import datetime
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.models import Employee, Notification, Payroll, Attendance, Leave,Performance
from django.contrib.auth.decorators import login_required
from employee.context_processors import user_info
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from django.db.models import Sum, F

def wellcome(request):
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        employee = None

    context = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'employee': employee
    }
    return render(request, 'employee/wellcome.html', context)

@login_required
def EmpAttendance(request):
    try:
        employee = request.user.employee
        attendance_records = Attendance.objects.filter(employee=employee)

        if 'month' in request.GET:
            month = request.GET['month']
            try:
                date = datetime.strptime(month, '%Y-%m')
                attendance_records = attendance_records.filter(date__year=date.year, date__month=date.month)
            except ValueError:
                messages.error(request, 'Invalid month format.')

        return render(request, 'employee/attendance.html', {'attendance_records': attendance_records})
    except Employee.DoesNotExist:
        messages.error(request, 'You are not associated with any employee record.')
        return redirect('wellcome')

@login_required
def payroll(request):
    try:
        employee = request.user.employee
        payrolls = Payroll.objects.filter(employee=employee)

        if 'month' in request.GET:
            month = request.GET['month']
            try:
                date = datetime.strptime(month, '%Y-%m')
                payrolls = payrolls.filter(month=date.month, year=date.year)
            except ValueError:
                messages.error(request, 'Invalid month format.')

        return render(request, 'employee/payroll.html', {'payrolls': payrolls})
    except Employee.DoesNotExist:
        messages.error(request, 'You are not associated with any employee record.')
        return redirect('wellcome')

@login_required
def payroll_detail(request, payroll_id):
    payroll = get_object_or_404(Payroll, id=payroll_id, employee=request.user.employee)
    context = {
        'payroll': payroll,
    }
    return render(request, 'employee/payroll_detail.html', context)

@login_required
def EmpLeave(request):
    if request.method == 'POST':
        leave_type = request.POST.get('leave_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        image = request.FILES.get('image')  

        employee = request.user.employee

        current_year = datetime.now().year

        
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        days_applied = (end_date - start_date).days + 1


        max_annual_leave_days = 30

        if leave_type == 'Annual':
            
            if days_applied > max_annual_leave_days:
                messages.error(request, f'You can only apply for a maximum of {max_annual_leave_days} days of annual leave at once.')
                return redirect('EmpLeave')

           
            annual_leave_taken = Leave.objects.filter(
                employee=employee,
                leave_type='Annual',
                start_date__year=current_year
            ).aggregate(total_days=Sum(F('end_date') - F('start_date') + timedelta(days=1)))['total_days'] or 0

            remaining_days = max_annual_leave_days - annual_leave_taken

           
            if remaining_days <= 0:
                messages.error(request, 'You have already used your annual leave for this year.')
                return redirect('EmpLeave')

           
            if days_applied > remaining_days:
                messages.error(request, f'You can only apply for {remaining_days} more days of annual leave this year.')
                return redirect('EmpLeave')

        if leave_type not in ['Sick', 'Maternity', 'Paternity']:
            one_year_ago = datetime.now().date() - timedelta(days=365)
            if employee.hire_date > one_year_ago:
                messages.error(request, 'Only employees who have been employed for 1 year or more can apply for this type of leave.')
                return redirect('EmpLeave')

            if leave_type in ['Casual', 'Vacation', 'Unpaid']:
                combined_leave_count = Leave.objects.filter(
                    employee=employee,
                    leave_type__in=['Casual', 'Vacation', 'Unpaid'],
                    start_date__year=current_year
                ).count()
                if combined_leave_count >= 3:
                    messages.error(request, 'Casual, Vacation, and Unpaid leave can only be taken a total of 3 times per year.')
                    return redirect('EmpLeave')

            elif leave_type == 'Education':
                education_leave_count = Leave.objects.filter(employee=employee, leave_type='Education', start_date__year=current_year).count()
                if education_leave_count >= 2:
                    messages.error(request, 'Educational leave can only be taken twice a year.')
                    return redirect('EmpLeave')

       
        if Leave.objects.filter(employee=employee, leave_type=leave_type, start_date=start_date).exists():
            messages.error(request, 'A leave with the same type and start date already exists for this employee.')
            return redirect('EmpLeave')

       
        leave = Leave.objects.create(
            employee=employee,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            status='Pending',
            image=image  
        )

       
        hr_users = User.objects.filter(groups__name='HR')
        for hr_user in hr_users:
            Notification.objects.create(
                user=hr_user,
                message=f'Employee {employee.first_name} {employee.last_name} has applied for leave from {start_date} to {end_date}.',
                leave=leave
            )

        messages.success(request, 'Leave request submitted successfully!')
        return redirect('EmpLeave')

    return render(request, 'employee/leave.html')

@login_required
def inbox(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'employee/inbox.html', {'notifications': notifications})

@login_required
def mark_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('inbox')

@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if not request.user.check_password(old_password):
            messages.error(request, 'Old password is incorrect.')
        elif new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password1) < 8:
            messages.error(request, 'New password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_passwordEmp')

    return render(request, 'employee/change_password.html')

@login_required
def EmpEvaluation(request):
    try:
        employee = request.user.employee
        evaluation_records = Performance.objects.filter(employee=employee)

        if 'month' in request.GET:
            month = request.GET['month']
            try:
                date = datetime.strptime(month, '%Y-%m')
                evaluation_records = evaluation_records.filter(date__year=date.year, date__month=date.month)
            except ValueError:
                messages.error(request, 'Invalid month format.')

        return render(request, 'employee/evaluation.html', {'evaluation_records': evaluation_records})
    except Employee.DoesNotExist:
        messages.error(request, 'You are not associated with any employee record.')
        return redirect('wellcome')


