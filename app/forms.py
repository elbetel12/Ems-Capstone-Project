from django import forms
from .models import Attendance

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'morning_check_in', 'morning_check_out', 'afternoon_check_in', 'afternoon_check_out']
        widgets = {
            'morning_check_in': forms.TimeInput(attrs={'type': 'time'}),
            'morning_check_out': forms.TimeInput(attrs={'type': 'time'}),
            'afternoon_check_in': forms.TimeInput(attrs={'type': 'time'}),
            'afternoon_check_out': forms.TimeInput(attrs={'type': 'time'}),
        }
