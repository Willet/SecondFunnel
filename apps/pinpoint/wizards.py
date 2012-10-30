from django.contrib.contenttypes.models import ContentType
from django.utils import simplejson as json
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse

from apps.assets.models import Product, ProductMedia, GenericMedia
from apps.pinpoint.models import (BlockType, BlockContent, Campaign,
    FeaturedProductBlock)
from apps.pinpoint.forms import FeaturedProductWizardForm

def _editing_valid_form(form, product):
    campaign = Campaign.objects.get(id = form.cleaned_data['campaign_id'])
    campaign.name = form.cleaned_data['name']
    campaign.description = form.cleaned_data['page_description']
    block_content = campaign.content_blocks.all()[0]
    block_content.data.product = product
    if form.cleaned_data['product_media_id']:
        product_media = ProductMedia.objects.get(
            pk = form.cleaned_data['product_media_id'])

        block_content.data.custom_image = None
        block_content.data.existing_image = product_media
        block_content.data.save()

    elif form.cleaned_data['generic_media_id']:
        try:
            custom_image = GenericMedia.objects.get(
                pk = form.cleaned_data['generic_media_id'])
        except GenericMedia.DoesNotExist:
            # missing media object. deal with this how?
            pass
        else:
            block_content.data.existing_image = None
            block_content.data.custom_image = custom_image
            block_content.data.save()
    if not block_content in campaign.content_blocks.all():
        campaign.content_blocks.clear()
        campaign.content_blocks.add(block_content)
    campaign.save()
    return campaign


def _creating_valid_form(block_type, form, product, store, preview=False):
    featured_product_data = FeaturedProductBlock(
        product = product,
        description = form.cleaned_data['description']
    )
    # existing product media was selected
    if form.cleaned_data['product_media_id']:
        product_media = ProductMedia.objects.get(
            pk = form.cleaned_data['product_media_id'])

        featured_product_data.existing_image = product_media

    # handle file upload
    elif form.cleaned_data['generic_media_id']:
        try:
            custom_image = GenericMedia.objects.get(
                pk = form.cleaned_data['generic_media_id'])
        except GenericMedia.DoesNotExist:
            # missing media object. deal with this how?
            pass
        else:
            featured_product_data.custom_image = custom_image
    featured_product_data.save()
    block_content = BlockContent(
        block_type = block_type,
        content_type = ContentType.objects.get_for_model(
            FeaturedProductBlock),
        object_id = featured_product_data.id
    )
    campaign = Campaign(
        store = store,
        name = form.cleaned_data['name'],
        description = form.cleaned_data['page_description'],
        live = not preview
    )
    block_content.save()
    campaign.save()
    campaign.content_blocks.add(block_content)
    return campaign


def _form_is_valid(block_type, form, store, preview=False):
    product = Product.objects.get(id = form.cleaned_data['product_id'])
    # we're editing the form
    if form.cleaned_data['campaign_id']:
        campaign = _editing_valid_form(form, product)

    else:
        campaign = _creating_valid_form(block_type, form, product, store, preview)

    if not preview:
        return HttpResponseRedirect(
            reverse('store-admin',
                    kwargs = {'store_id': store.id})
        )
    else:
        response = json.dumps({
            "success": True,
            "url": reverse('campaign', kwargs={'campaign_id': campaign.id})
        })
        return HttpResponse(response, mimetype='application/json')


def featured_product_wizard(request, store, block_type, campaign=None):
    preview = request.is_ajax()

    if request.method == 'POST':
        form = FeaturedProductWizardForm(request.POST, request.FILES)

        if form.is_valid():
            return _form_is_valid(block_type, form, store, preview)
    else:
        if campaign:
            initial_data = {
                "name": campaign.name,
                "product_id": campaign.content_blocks.all()[0].data.product.id,
                "page_description": campaign.description,
                "description": campaign.content_blocks.all()[0].data.description,
                "campaign_id": campaign.id,
            }

            product_image = campaign.content_blocks.all()[0].data.get_image()

            if product_image.__class__.__name__ == "GenericMedia":
                initial_data["generic_media_id"] = product_image.id

            elif product_image.__class__.__name__ == "ProductMedia":
                initial_data["product_media_id"] = product_image.id

            form = FeaturedProductWizardForm(initial_data)
        else:
            form = FeaturedProductWizardForm()

    if not preview:
        return render_to_response('pinpoint/wizards/%s/ui.html' % block_type.slug, {
            "store": store,
            "block_types": BlockType.objects.all(),
            "products": store.product_set.all(),
            "form": form,
            "campaign": campaign,
        }, context_instance=RequestContext(request))

    else:
        return HttpResponse(json.dumps({"success": False}), mimetype='application/json')