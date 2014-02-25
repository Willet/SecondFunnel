#!/usr/bin/env python
# python this_file.py username email password

import sys

from django.contrib.auth.models import User

if User.objects.count() == 0 and len(sys.argv) >= 4:
    admin = User.objects.create_user(sys.argv[1], sys.argv[2], sys.argv[3])
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()
elif len(sys.argv) == 1:  # no args
    admin = User.objects.create_user("admin", "admin@willetinc.com", "secretpassword")
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()
