from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.contenttypes.models import ContentType

from apps.assets.models import Product
from apps.pinpoint.models import BlockType, BlockContent, Campaign
from apps.pinpoint.forms import FeaturedProductWizardForm


def featured_product_wizard(request, store, block_type):
    if request.method == 'POST':
        form = FeaturedProductWizardForm(request.POST)

        if form.is_valid():

            block_content = BlockContent(
                block_type=block_type,
                content_type=ContentType.objects.get_for_model(Product),
                object_id=form.cleaned_data['product_id']
            )

            campaign = Campaign(
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
            )

            return HttpResponseRedirect('/')
    else:
        form = FeaturedProductWizardForm()

    return render_to_response('pinpoint/wizards/%s/ui.html' % block_type.slug, {
        "store": store,
        "block_types": BlockType.objects.all(),
        "products": store.product_set.all(),
        "form": form,
    }, context_instance=RequestContext(request))
