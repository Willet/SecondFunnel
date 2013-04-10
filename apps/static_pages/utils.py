from django.contrib.contenttypes.models import ContentType

from apps.static_pages.models import StaticLog

def save_static_log(object_class, object_id, key):
    object_type = ContentType.objects.get_for_model(object_class)
    log_record = StaticLog(
        content_type=object_type, object_id=object_id, key=key)
    log_record.save()
