from django.urls import path
from EMS import settings
from . import views
from django.conf.urls.static import static


urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # path('no_permission/', views.no_permission, name='no_permission'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)