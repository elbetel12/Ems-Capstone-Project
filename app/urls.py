from django.urls import path

from EMS import settings
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path('', views.Dashboard, name='dashboard'),
    
    path('attendance', views.attendance, name='attendance'),
    path('report', views.report, name='report'),
    path('profile', views.profile, name='profile'),
    

    path('add_employee', views.employee, name='add_employee'),
    path('list_employees/', views.list_employees, name='list_employees'),
    path('edit_employee/<int:id>/', views.edit_employee, name='edit_employee'), 
    path('delete_employee/<int:id>/', views.delete_employee, name='delete_employee'),
    path('employee/<int:employee_id>/', views.employee_detail, name='employee_detail'),

    path('edit_leave/<int:id>/', views.edit_leave, name='edit_leave'), 
    path('delete_leave/<int:id>/', views.delete_leave, name='delete_leave'),
    path('list_leave', views.list_leave, name='list_leave'),
    path('add_leave', views.add_leave, name='add_leave'),

    path('list_departments/', views.list_departments, name='list_departments'),
    path('add_department/', views.add_department, name='add_department'),
    path('edit_department/<int:id>/', views.edit_department, name='edit_department'), 
    path('delete_department/<int:id>/', views.delete_department, name='delete_department'),

    path('list_payrolls/', views.list_payrolls, name='list_payrolls'),
    path('payroll_invoice/<int:id>/', views.payroll_invoice, name='payroll_invoice'),

     path('work_hours_report', views.work_hours_report, name='work_hours_report'),
     path('monthly_work_hours_report/', views.monthly_work_hours_report, name='monthly_work_hours_report'),

     path('save_attendance/', views.save_attendance, name='save_attendance'),
     path('edit_payroll/<int:payroll_id>/', views.edit_payroll, name='edit_payroll'),
     path('change_password', views.change_password, name='change_password'),
     path('qr_code_scan/', views.qr_code_scan, name='qr_code_scan'),

     path('fetch_notifications/', views.fetch_notifications, name='fetch_notifications'),
     path('notifications/mark_as_read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
     path('scan_qr/', views.qr_code_scanner, name='scan_qr'),
     path('manual_attendance/', views.manual_attendance, name='manual_attendance'),
     path('attendance_list/', views.attendance_list, name='attendance_list'),
     path('edit_attendance/<int:attendance_id>/', views.edit_attendance, name='edit_attendance'),
     path('notifications/mark_as_read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
     path('employee/<int:employee_id>/evaluate/', views.evaluate_employee, name='evaluate_employee'),
     path('generatepayroll/', views.generate_payroll, name='generate_payroll'),
     path('evaluations/', views.list_evaluations, name='list_evaluations'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
