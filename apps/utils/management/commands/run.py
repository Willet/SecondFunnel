"""
Run *any* importable function inside the django shell. First argument must be a string.
"""
import importlib

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        module = importlib.import_module(args[0])
        try:
            return getattr(module, args[1])(*args[2:], **kwargs)
        except:
            return module(*args[1:], **kwargs)
