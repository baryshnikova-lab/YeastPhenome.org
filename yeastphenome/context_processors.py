from django.conf import settings

def globals(request):
    """Returns a dict of defaults to be used by templates, if configured
    correcty in the settings.py file."""
    return {'TITLE': settings.TITLE}
