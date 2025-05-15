from django.core.management.base import BaseCommand
from app.models import UserForEmployee, Employee

class Command(BaseCommand):
    help = 'Ensure that every UserForEmployee entry is properly reflected in the Employee model'

    def handle(self, *args, **kwargs):
        user_for_employees = UserForEmployee.objects.all()
        for user_for_employee in user_for_employees:
            employee = user_for_employee.employee
            user = user_for_employee.user
            if employee.user != user:
                employee.user = user
                employee.save()
                self.stdout.write(self.style.SUCCESS(f'Updated user for employee {employee.first_name} {employee.last_name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'No update needed for employee {employee.first_name} {employee.last_name}'))
