from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from apps.assets.models import Product, ProductMedia, GenericMedia
from apps.pinpoint.models import (BlockType, BlockContent, Campaign,
    FeaturedProductBlock)
from apps.pinpoint.forms import FeaturedProductWizardForm


def featured_product_wizard(request, store, block_type):
    if request.method == 'POST':
        form = FeaturedProductWizardForm(request.POST, request.FILES)

        if form.is_valid():
            product = Product.objects.get(id=form.cleaned_data['product_id'])

            featured_product_data = FeaturedProductBlock(
                product=product,
                description=form.cleaned_data['description']
            )

            # existing product media was selected
            if form.cleaned_data['product_media_id']:
                product_media = ProductMedia.objects.get(
                    id=form.cleaned_data['product_media_id'])

                featured_product_data.existing_image = product_media

            # handle file upload
            elif request.FILES['product_image']:
                custom_image = GenericMedia(
                    media_type="img",
                    hosted=request.FILES['product_image']
                )
                custom_image.save()

                featured_product_data.custom_image = custom_image

            featured_product_data.save()

            block_content = BlockContent(
                block_type=block_type,
                content_type=ContentType.objects.get_for_model(
                    FeaturedProductBlock),
                object_id=featured_product_data.id
            )

            campaign = Campaign(
                store=store,
                name=form.cleaned_data['name'],
                description=form.cleaned_data['page_description'],
            )

            block_content.save()
            campaign.save()

            campaign.content_blocks.add(block_content)

            return HttpResponseRedirect(
                reverse('store-admin', kwargs={'store_id': store.id})
            )
    else:
        form = FeaturedProductWizardForm()

    return render_to_response('pinpoint/wizards/%s/ui.html' % block_type.slug, {
        "store": store,
        "block_types": BlockType.objects.all(),
        "products": store.product_set.all(),
        "form": form,
    }, context_instance=RequestContext(request))
