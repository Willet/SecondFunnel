#!/usr/bin/env python
# python this_file.py username email password

import sys

from django.contrib.auth.models import User

if User.objects.count() == 0 and len(sys.argv) == 3:
    admin = User.objects.create_user(sys.argv[0], sys.argv[1], sys.argv[2])
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()
