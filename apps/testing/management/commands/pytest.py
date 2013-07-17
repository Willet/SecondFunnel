from django.core.management.base import BaseCommand, CommandError

from optparse import make_option


class Command(BaseCommand):
    """
    User-interface class for running the Python tests.  The tests ensure that the generated
    HTML code is correct, the Django server runs correctly and that the page runs properly.
    
    """

    def handle(self, *args, **options):
        pass
