from django.conf import settings


def environment(request):
    # Access environment variable in templates
    return {'ENVIRONMENT': settings.ENVIRONMENT}
