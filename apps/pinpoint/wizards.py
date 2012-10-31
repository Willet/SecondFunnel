from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from apps.assets.models import Product, ProductMedia, GenericMedia
from apps.pinpoint.models import (BlockType, BlockContent, Campaign,
    FeaturedProductBlock)
from apps.pinpoint.forms import FeaturedProductWizardForm


def featured_product_wizard(request, store, block_type, campaign=None):
    if request.method == 'POST':
        form = FeaturedProductWizardForm(request.POST, request.FILES)

        if form.is_valid():
            product = Product.objects.get(pk=form.cleaned_data['product_id'])

            generic_media_id = form.cleaned_data.get("generic_media_id")
            product_media_id = form.cleaned_data.get("product_media_id")

            has_product_media = product_media_id and \
                    ProductMedia.objects.filter(pk=product_media_id).exists()

            # we're editing the form
            if form.cleaned_data['campaign_id']:
                campaign = Campaign.objects.get(pk=form.cleaned_data['campaign_id'])

                campaign.name = form.cleaned_data['name']
                campaign.description = form.cleaned_data['page_description']

                block_content = campaign.content_blocks.all()[0]
                block_content.data.product = product

                # existing product media was selected
                if has_product_media:
                    block_content.data.custom_image = None
                    block_content.data.existing_image = ProductMedia.objects.get(
                            pk=product_media_id)
                    block_content.data.save()
                # an image was uploaded (the form checks that one of these must exist)
                else:
                    block_content.data.existing_image = None
                    block_content.data.custom_image = GenericMedia.objects.get(
                            pk=generic_media_id)
                    block_content.data.save()

                if not block_content in campaign.content_blocks.all():
                    campaign.content_blocks.clear()
                    campaign.content_blocks.add(block_content)

                campaign.save()

            else:
                featured_product_data = FeaturedProductBlock(
                    product=product,
                    description=form.cleaned_data['description']
                )

                # existing product media was selected
                if has_product_media:
                    featured_product_data.existing_image = ProductMedia.objects.get(
                            pk=product_media_id)
                # an image was uploaded (the form checks that one of these must exist)
                else:
                    featured_product_data.custom_image = GenericMedia.objects.get(
                            pk=generic_media_id)

                featured_product_data.save()

                block_content = BlockContent(
                    block_type=block_type,
                    content_type=ContentType.objects.get_for_model(
                        FeaturedProductBlock),
                    object_id=featured_product_data.pk
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
                reverse('campaign-overview-admin',
                    kwargs={'store_id': store.pk, 'campaign_id': campaign.pk})
            )
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

    return render_to_response('pinpoint/wizards/%s/ui.html' % block_type.slug, {
        "store": store,
        "block_types": BlockType.objects.all(),
        "products": store.product_set.all(),
        "form": form,
        "campaign": campaign,
    }, context_instance=RequestContext(request))
