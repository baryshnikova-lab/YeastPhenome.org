from django import template

register = template.Library()

@register.simple_tag
def active(text, pattern):
    if pattern == text:
        return 'active'
    return 'inactive'