from django.contrib.auth.models import User
from tastypie.resources import ModelResource


class UserResource(ModelResource):
    class Meta:
        resource_name = 'login'
        queryset = User.objects.all()
        excludes = ['id', 'email', 'password', 'is_staff', 'is_superuser']