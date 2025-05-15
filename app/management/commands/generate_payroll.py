from django.core.management.base import BaseCommand
from app.models import Employee, Payroll, Notification
from app.management.commands.calculate_hours import calculate_total_hours
import decimal
import datetime

class Command(BaseCommand):
    help = 'Generate payroll for all employees for a specific month and year'

    def add_arguments(self, parser):
        parser.add_argument('pay_date', nargs='?', type=str, help='The date for the payroll in YYYY-MM-DD format')

    def handle(self, *args, **kwargs):
        pay_date_str = kwargs['pay_date']
        
        if pay_date_str:
            pay_date = datetime.time.strptime(pay_date_str, '%Y-%m-%d').date()
        else:
            pay_date = datetime.date.today()  # Use current date if no date provided
        
        month = pay_date.month
        year = pay_date.year
        
        employees = Employee.objects.all()
        
        for employee in employees:
            # Calculate total hours worked
            total_hours = decimal.Decimal(calculate_total_hours(employee, month, year))

            # Calculate base salary and hourly rate
            base_salary = employee.salary
            standard_hours = decimal.Decimal('160')  # Assume 160 hours in a full month
            hourly_rate = base_salary / standard_hours

            # Calculate the earned salary based on hours worked
            earned_salary = total_hours * hourly_rate

            # Apply deductions if needed (e.g., if total hours are below a threshold)
            threshold_hours = decimal.Decimal('160')
            deduction_per_hour = decimal.Decimal('10')
            
            if total_hours < threshold_hours:
                additional_deductions = (threshold_hours - total_hours) * deduction_per_hour
            else:
                additional_deductions = decimal.Decimal('0')
            
            # Deduct the amount from earned salary
            deductions = additional_deductions
            
            # Taxes calculation
            taxable_income = earned_salary - deductions
            taxes = taxable_income * decimal.Decimal('0.2')  # 20% tax rate
            
            # Calculate net pay
            net_pay = earned_salary - deductions - taxes

            # Check if there's no payroll due to no hours worked
            if total_hours == 0:
                # Send a notification that no payroll was generated
                if employee.user:
                    try:
                        Notification.objects.create(
                            user=employee.user,
                            message=f'No payroll recived for {month}/{year} due to no hours worked.',
                        )
                    except Exception as e:
                        print(f"Failed to create notification for employee {employee.first_name} {employee.last_name}: {e}")
            else:
                # Generate payroll
                payroll = Payroll(
                    employee=employee,
                    pay_date=pay_date,
                    month=month,
                    year=year,
                    base_salary=earned_salary,  # Use earned salary here
                    bonuses=decimal.Decimal('0'),  # Assume no bonuses in this case
                    deductions=deductions,
                    taxes=taxes,
                    net_pay=net_pay
                )
                payroll.save()

                # Create a notification for the employee if associated with a user
                if employee.user:
                    try:
                        Notification.objects.create(
                            user=employee.user,
                            message=f'Your payroll for {month}/{year} has been generated.',
                        )
                    except Exception as e:
                        print(f"Failed to create notification for employee {employee.first_name} {employee.last_name}: {e}")

        if pay_date_str:
            self.stdout.write(self.style.SUCCESS(f'Successfully generated payroll for all employees on {pay_date_str}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully generated payroll for all employees on {pay_date}'))
