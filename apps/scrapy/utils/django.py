from apps.assets.models import Product


def django_item_values(item):
    # Modified from DjangoItem.instance
    return ((k, item.get(k)) for k in item._values if k in item._model_fields)


def item_to_model(item):
    model_class = getattr(item, 'django_model')
    if not model_class:
        raise TypeError("Item is not a `DjangoItem` or is misconfigured")

    return item.instance


def get_or_create(item):
    model = item_to_model(item)
    model_class = type(model)
    created = False

    # Normally, we would use `get_or_create`. However, `get_or_create` would
    # match all properties of an object (i.e. create a new object
    # anytime it changed) rather than update an existing object.
    #
    # Instead, we do the two steps separately

    # if there is a lookup that provides a unique-match
    # it should be merged with that item.
    # e.g. ScraperProduct uniqueness is (('store_id', 'sku', 'name'),)
    uniqueness = getattr(item, 'uniqueness', ())
    for uniq_attributes in uniqueness:
        lookup_dict = {}
        for attr in uniq_attributes:
            if attr in item:
                lookup_dict[attr] = item.get(attr)
            else:
                # if there isn't that attribute, it can't provide uniqueness
                continue

        try:
            obj = model_class.objects.get(**lookup_dict)
            break  # found a match :)
        except model_class.DoesNotExist:
            obj = None

    # if a match was not found, create a new model
    if obj is None:
        created = True
        obj = model  # djangoitem created a model for us.

    return (obj, created)


def update_model(destination, source_item, commit=True):
    pk = destination.pk

    for (key, value) in django_item_values(source_item):
        setattr(destination, key, value)

    setattr(destination, 'pk', pk)

    if commit:
        destination.save()

    return destination
