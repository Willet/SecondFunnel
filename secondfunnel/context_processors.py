from django.conf import settings

def expose_settings(request):
    if settings.EXPOSED_SETTINGS is not None:
        return settings.EXPOSED_SETTINGS
    else:
        return {}
