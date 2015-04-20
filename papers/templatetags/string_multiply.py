from django.template import Library

register = Library()

@register.filter
def multiply(string, times):
    return string * times