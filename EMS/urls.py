from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static

from EMS import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('apps/',include('app.urls')),
    path('employee/',include('employee.urls')),
    path('',include('accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)