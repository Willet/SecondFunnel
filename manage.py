#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secondfunnel.settings"
                                                    ".dev")

    test_env = (os.getenv('DEFAULT_ENV') or os.getenv('PARAM1')) == 'TEST'
    demo_env = (os.getenv('DEFAULT_ENV') or os.getenv('PARAM1')) == 'DEMO'

    if test_env:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'secondfunnel.settings.test'

    if demo_env:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'secondfunnel.settings.demo'

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
