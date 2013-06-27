from django.conf import settings


def environment(request):
    # Access environment variable in templates
    return {'ENVIRONMENT': settings.ENVIRONMENT}


def required_dimensions(request):
    # Constants for required media dimensions
    return { 'MIN_MEDIA_WIDTH': settings.MIN_MEDIA_WIDTH,
             'MIN_MEDIA_HEIGHT': settings.MIN_MEDIA_HEIGHT
           }
