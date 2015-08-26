import inspect

from . import pipelines

# Pipelines can be imported directly from the module
to_export = [(name, ref) for (name, ref) in inspect.getmembers(pipelines, inspect.isclass) \
             if 'Pipeline' in name]
globals().update(to_export)
__all__ = [ref for _, ref in to_export]