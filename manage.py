#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secondfunnel.settings"
                                                    ".dev")
    
    # We use PARAM1 because it is the only one available in Elastic Beanstalk
    # It should be replaced with a more reasonable environment variable like
    # `ENVIRONMENT_TYPE` or something similar
    test_env = os.getenv('PARAM1') == 'TEST'
    demo_env = os.getenv('PARAM1') == 'DEMO'

    if test_env:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'secondfunnel.settings.test'

    if demo_env:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'secondfunnel.settings.demo'

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
