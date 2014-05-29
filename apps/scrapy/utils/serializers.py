def django_serializer(value):
    return value.id  # serializers.serialize('json', [ value, ])


def store_serializer(value):
    return django_serializer(value)