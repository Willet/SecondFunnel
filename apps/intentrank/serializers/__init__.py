from apps.utils.functional import autodiscover_module_classes

from .utils import IRSerializer

# All serializers can be directly imported from this module
to_export = autodiscover_module_classes(__name__, __path__, IRSerializer)
globals().update(to_export)
__all__ = [ref for _, ref in to_export]