from django import template

register = template.Library()

@register.filter
def is_hr(user):
    return user.groups.filter(name='HR').exists()
