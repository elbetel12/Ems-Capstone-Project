from .models import UserForDepartmentHead, Notification

def department_head_context(request):
    context = {}
    if request.user.is_authenticated:
        try:
            department_head = UserForDepartmentHead.objects.get(user=request.user)
            context['department_head'] = department_head
        except UserForDepartmentHead.DoesNotExist:
            pass
    return context


def notification_context_processor(request):
    if request.user.is_authenticated and request.user.groups.filter(name='HR').exists():
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        unread_notifications_count = notifications.count()
        return {
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
        }
    return {}

def notification_count_processor(request):
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {
            'unread_notifications_count': unread_notifications_count,
        }
    return {}
