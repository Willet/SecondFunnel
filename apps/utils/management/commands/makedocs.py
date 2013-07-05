import os

from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):
    args = ''
    help = 'Creates documentation for the SecondFunnel project.'
    folders_to_include = [
        'apps/',
        'secondfunnel/',
        'scripts/',
        'manage.py',
        'terrain.py',
    ]

    def handle_noargs(self, **kwargs):
        os.system("epydoc -v --parse-only -name SecondFunnel -o doc " + " ".join(self.folders_to_include))
