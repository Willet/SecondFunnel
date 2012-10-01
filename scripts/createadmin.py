from django.contrib.auth.models import User

if User.objects.count() == 0:
    admin = User.objects.create_user(
        'grigory', 'grigory.kruglov@gmail.com', 'grigory.kruglov@gmail.com')
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()
