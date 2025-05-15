from datetime import datetime, timedelta
from app.models import Attendance

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