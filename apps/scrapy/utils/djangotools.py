#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.core.exceptions import MultipleObjectsReturned

from apps.assets.models import Product, Category, Content


def django_item_values(item):
    # Modified from DjangoItem.instance
    return ((k, item.get(k)) for k in item._values if k in item._model_fields)


def item_to_model(item):
    model_class = getattr(item, 'django_model')
    if not model_class:
        raise TypeError("Item is not a `DjangoItem` or is misconfigured")

    return item.instance


def get_or_create(model):
    """
    Normally, we would use Django's `get_or_create`. However, `get_or_create`
    would match all properties of an object (i.e. create a new object anytime it
    changed) rather than update an existing object.

    Instead, this does a lookup on a narrow set of reliably distinct fields.
    Update should be manually performed by update_model (see below)

    NOTE: if model is Product and multiple Product's are found, they are merged here.
    Tile serialization is disabled for this merge and can leave the database in a bad state.
    Be very careful to run tile serialization soon after this.

    Returns: <tuple> (<model_class> obj, <bool> created)
    """
    model_class = type(model)

    def get_or_return(model, query):
        try:
            obj = model_class.objects.get(**query)
            return (obj, False)
        except model_class.DoesNotExist:
            return (model, True) # djangoitem created a model for us.

    def get_or_return_product(model, query):
        # Occasionally we can get multiples of products. Merge if we find them
        try:
            (product, created) = get_or_return(model, query)
        except MultipleObjectsReturned:
            qs = Product.objects.filter(**query)
            product = Product.merge_products(qs)
            created = False
        return (product, created)
    
    if isinstance(model, Product):
        # We have no unique identifier at the moment; use the url / store
        return get_or_return_product(model, { 'url': model.url, 'store_id': model.store.id })
    elif isinstance(model, Content):
        # since there is no unique identifier for content, assuming source_url is unique
        return get_or_return(model, { 'source_url': model.source_url })
    elif isinstance(model, Category):
        return get_or_return(model, { 'name': model.name, 'store_id': model.store.id })
    else:
        # Don't know what this is, pass it on
        return (model, False)


def update_model(destination, source_item, commit=True):
    pk = destination.pk
    
    # Persist exisitng attributes (arbitrary data field)
    attrs = destination.get('attributes', {}).copy()
    attrs.update(source_item.get('attributes', {}))
    source_item['attributes'] = attrs
    for (key, value) in django_item_values(source_item):
        setattr(destination, key, value)

    setattr(destination, 'pk', pk)

    if commit:
        destination.save()
    
    return destination
