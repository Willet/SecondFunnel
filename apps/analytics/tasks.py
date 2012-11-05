from celery import task

from apps.analytics.settings import INSTALLED_ANALYTICS, ANALYTICS_CLASS_NAME
import apps.analytics.storage_backends as storage_backends


@task()
def analytics_periodic():
    """Dynamically loads storage backends of installed analytics modules
    and tells storage backend to start the appropriate cron job.

    First load the appropriate storage backend.
    Use it to initialize analyitcs instance.
    """

    for module in INSTALLED_ANALYTICS.keys():

        StorageBackend = getattr(storage_backends,
            INSTALLED_ANALYTICS[module]["storage_backend"]
        )

        storage_backend = StorageBackend()

        _analytics_processes = __import__(
            "apps.analytics.%s.tasks" % module,
            globals(), locals(), [ANALYTICS_CLASS_NAME], -1
        )

        AnalyticsPeriodic = getattr(_analytics_processes, ANALYTICS_CLASS_NAME)

        analytics_instance = AnalyticsPeriodic(storage_backend)
        analytics_instance.start()
