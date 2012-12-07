#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secondfunnel.settings"
                                                    ".dev")

    args = sys.argv

    # This forces all migrations to have the same name.
    # We do this so that we can tell when there are migration conflicts when
    #   merging.
    if (len(sys.argv) >= 2 and sys.argv[1] == 'schemamigration'):
        args.append('auto')

    from django.core.management import execute_from_command_line

    execute_from_command_line(args)
