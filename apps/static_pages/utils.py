from django.contrib.contenttypes.models import ContentType

from apps.static_pages.models import StaticLog
from apps.assets.models import Store


def save_static_log(object_class, object_id, key):
    object_type = ContentType.objects.get_for_model(object_class)
    log_record = StaticLog(
        content_type=object_type, object_id=object_id, key=key)
    log_record.save()


def remove_static_log(object_class, object_id, key):
    object_type = ContentType.objects.get_for_model(object_class)
    log_records = StaticLog.objects.filter(
        content_type=object_type, object_id=object_id, key=key).delete()


def bucket_exists_or_pending(store):
    store_type = ContentType.objects.get_for_model(Store)

    log_records = StaticLog.objects.filter(
            content_type=store_type, object_id=store.id)

    return len(log_records) > 1
