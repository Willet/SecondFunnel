from apps.assets.models import Product, Content


def django_item_values(item):
    # Modified from DjangoItem.instance
    return ((k, item.get(k)) for k in item._values if k in item._model_fields)


def item_to_model(item):
    model_class = getattr(item, 'django_model')
    if not model_class:
        raise TypeError("Item is not a `DjangoItem` or is misconfigured")

    return item.instance


def get_or_create(model):
    model_class = type(model)
    created = False

    # Normally, we would use `get_or_create`. However, `get_or_create` would
    # match all properties of an object (i.e. create a new object
    # anytime it changed) rather than update an existing object.
    #
    # Instead, we do the two steps separately
    try:
        if isinstance(model, Product):
            # We have no unique identifier at the moment; use the sku / store
            obj = model_class.objects.get(sku=model.sku, store_id=model.store_id)
        elif isinstance(model, Content):
            # since there is no unique identifier for content, assuming source_url is unique
            obj = model_class.objects.get(source_url=model.source_url)
        else:  # if not a product, its content? this is here just in case
            # TODO: don't always create...
            created = True
            obj = model  # djangoitem created a model for us.
    except model_class.DoesNotExist:
        created = True
        obj = model  # djangoitem created a model for us.

    return (obj, created)


def update_model(destination, source_item, commit=True):
    pk = destination.pk
    
    # Presist exisitng attributes (arbitrary data field)
    attrs = destination.get('attributes', {}).copy()
    attrs.update(source_item.get('attributes', {}))
    source_item['attributes'] = attrs

    for (key, value) in django_item_values(source_item):
        setattr(destination, key, value)

    setattr(destination, 'pk', pk)

    if commit:
        destination.save()
    
    return destination
