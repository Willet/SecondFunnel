#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secondfunnel.settings.dev")

    # AWS_GROUP must be set by the deploy script
    # allowed values: production, stage
    environment_type = os.getenv("AWS_GROUP", "") or "dev"

    os.environ["DJANGO_SETTINGS_MODULE"] = \
        "secondfunnel.settings.{0}".format(environment_type.lower())

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
