#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secondfunnel.settings"
                                                    ".dev")
    
    # We use PARAM1 because it is the only one available in Elastic Beanstalk
    # It should be replaced with a more reasonable environment variable like
    # `ENVIRONMENT_TYPE` or something similar.
    # allowed values: DEMO, PRODUCTION, TEST
    environment_type = os.getenv('PARAM1', '').upper() or 'DEV'

    os.environ['DJANGO_SETTINGS_MODULE'] = 'secondfunnel.settings.{0}'.format(
        environment_type.lower())

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
