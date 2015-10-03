from contextlib2 import ContextDecorator
from django.db.models.signals import post_save, m2m_changed

# CIRCULAR IMPORTS - delay loading by not import specific things
import apps.assets.signals
import apps.assets.models


class disable_tile_serialization(ContextDecorator):
    """ Context manager that suppresses tile serialization until exit
        
        Useful when creating a new tile that requires multiple steps before serializing
        ex: adding multiple different m2m keys

        Can safely be nested
    """
    # Avoid pre-maturally re-enabling signals if this context manager is nested
    # Keep track of how many this has been entered
    disabled_counter = 0

    def __enter__(self):
        self.disabled_counter += 1
        try:
            post_save.disconnect(signals.tile_saved, sender=models.Tile)
            m2m_changed.disconnect(signals.tile_m2m_changed)
            m2m_changed.disconnect(signals.content_m2m_changed)
        except:
            # If disconnecting signals failed for any reason
            # re-connect signals if no wrapping context managers and re-raise
            try:
                self.__exit__(*sys.exc_info())
            except:
                # Suppress the 2nd exception
                pass
            raise

    def __exit__(self, type, value, traceback):
        self.disabled_counter -= 1
        if self.disabled_counter < 1:
            post_save.connect(signals.tile_saved, sender=models.Tile)
            m2m_changed.connect(signals.content_m2m_changed)
            m2m_changed.connect(signals.tile_m2m_saved)
            # Should never have exit'ed more than enter'ed.
            assert self.disabled_counter == 0
