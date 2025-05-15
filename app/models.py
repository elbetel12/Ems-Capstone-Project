from datetime import datetime, timedelta
import decimal
from django.db import models
from django.contrib.auth.models import User, Group

def calculate_total_hours(employee, month, year):
    attendance_records = Attendance.objects.filter(employee=employee, date__year=year, date__month=month)

    total_hours = timedelta()
    for record in attendance_records:
        if record.check_in and record.check_out:
            check_in_time = record.check_in.time()  
            check_out_time = record.check_out.time() 
            total_hours += (datetime.combine(record.date, check_out_time) -
                            datetime.combine(record.date, check_in_time))

    return total_hours.total_seconds() / 3600.0


class Department(models.Model):
    department_name = models.CharField(max_length=50)
    department_head = models.OneToOneField('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='head_of_department')
    description = models.TextField()
    is_active = models.BooleanField(default=True)  # Add this field

    def __str__(self):
        return self.department_name

class Employee(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    dob = models.DateField()
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    address = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    position = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    is_department_head = models.BooleanField(default=False, null=True)
    image = models.ImageField(upload_to='employee_images/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    qr_code_image = models.ImageField(upload_to='employee_qr_codes/', null=True, blank=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_department_head:
            self.department.department_head = self
            self.department.save()

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)  # Automatically set the date when the record is created
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('employee', 'date')

    def __str__(self):
        return f'Attendance for {self.employee} on {self.date}'


class Leave(models.Model):
    LEAVE_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]

    LEAVE_TYPE_CHOICES = [
        ('Sick', 'Sick'),
        ('Vacation', 'Vacation'),
        ('Maternity', 'Maternity'),
        ('Paternity', 'Paternity'),
        ('Unpaid', 'Unpaid'),
        ('Annual', 'Annual'),
        ('Casual', 'Casual'),
        ('Education', 'Education'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=LEAVE_STATUS_CHOICES, default='Pending')
    image = models.ImageField(upload_to='leave_paper/', null=True, blank=True)

    def __str__(self):
        return f'Leave {self.leave_type} for {self.employee} from {self.start_date} to {self.end_date}'

class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    pay_date = models.DateField()
    month = models.IntegerField(null=True)
    year = models.IntegerField(null=True)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonuses = models.DecimalField(max_digits=10, decimal_places=2)
    deductions = models.DecimalField(max_digits=10, decimal_places=2)
    taxes = models.DecimalField(max_digits=10, decimal_places=2)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.base_salary = self.employee.salary
        self.month = self.pay_date.month
        self.year = self.pay_date.year

        total_hours = decimal.Decimal(calculate_total_hours(self.employee, self.month, self.year))
        threshold_hours = decimal.Decimal('160')
        deduction_per_hour = decimal.Decimal('10')
   
        if total_hours < threshold_hours:
            additional_deductions = (threshold_hours - total_hours) * deduction_per_hour
        else:
            additional_deductions = decimal.Decimal('0')

        self.deductions += additional_deductions
        self.net_pay = self.base_salary + self.bonuses - self.deductions - self.taxes
        super(Payroll, self).save(*args, **kwargs)

    def __str__(self):
        return f'Payroll for {self.employee} on {self.pay_date}'



class UserForDepartmentHead(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.user:
            username = f'{self.employee.first_name.lower()}.{self.employee.last_name.lower()}'
            user = User.objects.create_user(username=username, password='password123')
            user.first_name = self.employee.first_name
            user.last_name = self.employee.last_name
            user.email = self.employee.email
            user.save()
            self.user = user
        
        # Add user to 'Manager' group
        manager_group, created = Group.objects.get_or_create(name='Manager')
        self.user.groups.add(manager_group)

        super().save(*args, **kwargs)

    def __str__(self):
        return f'Department Head: {self.employee.first_name} {self.employee.last_name}'
    
class UserForEmployee(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.user:
            username = f'{self.employee.first_name.lower()}.{self.employee.last_name.lower()}'
            user = User.objects.create_user(username=username, password='password123')
            user.first_name = self.employee.first_name
            user.last_name = self.employee.last_name
            user.email = self.employee.email
            user.save()
            self.user = user
        
        # Add user to 'Employe' group
        employe_group, created = Group.objects.get_or_create(name='Employe')
        self.user.groups.add(employe_group)

        # Update the employee's user field
        self.employee.user = self.user
        self.employee.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f'Employee: {self.employee.first_name} {self.employee.last_name}'
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    leave = models.ForeignKey(Leave, null=True, blank=True, on_delete=models.CASCADE)  # Add this field
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message
    

class Performance(models.Model):
    PERFORMANCE_RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Above Average'),
        (5, 'Excellent'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    rating = models.IntegerField(choices=PERFORMANCE_RATING_CHOICES)
    comments = models.TextField(null=True, blank=True)
    evaluated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='evaluations')

    def __str__(self):
        return f'Performance of {self.employee.first_name} {self.employee.last_name} on {self.date}'