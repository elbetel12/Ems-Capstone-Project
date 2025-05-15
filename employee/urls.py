from django.urls import path
from EMS import settings
from . import views
from django.conf.urls.static import static


urlpatterns = [
    path('wellcome/',views.wellcome,name='wellcome'),
    path('payroll/',views.payroll,name='payroll'),
    path('empattendance/',views.EmpAttendance,name='EmpAttendance'),
    path('empleave/',views.EmpLeave,name='EmpLeave'),
    path('payroll/<int:payroll_id>/', views.payroll_detail, name='payroll_detail'),
     path('inbox/', views.inbox, name='inbox'),
    path('inbox/mark-as-read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
    path('change_password/', views.change_password, name='change_passwordEmp'),
    path('evaluation/', views.EmpEvaluation, name='employee_evaluation'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)