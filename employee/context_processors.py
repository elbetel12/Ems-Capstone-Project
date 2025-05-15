from app.models import Employee
from app.models import Notification

def notification_count_processor(request):
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {
            'unread_notifications_count': unread_notifications_count,
        }
    return {}

def user_info(request):
    if request.user.is_authenticated:
        try:
            employee = Employee.objects.get(user=request.user)
            return {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'department': employee.department.department_name,
                'position': employee.position,
                'hire_date': employee.hire_date,
                'salary': employee.salary,
                'address': employee.address,
                'phone': employee.phone,
                'email': employee.email,
                'dob': employee.dob,
                'gender': employee.gender,
                'image': employee.image,
                'qr_code_image': employee.qr_code_image
            }
        except Employee.DoesNotExist:
            return {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            }
    return {}
