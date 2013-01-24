from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.utils import simplejson as json
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse

from apps.assets.models import Product, ProductMedia, GenericImage
from apps.pinpoint.models import (BlockType, BlockContent, Campaign,
    FeaturedProductBlock, ShopTheLookBlock)
from apps.pinpoint.forms import FeaturedProductWizardForm, ShopTheLookWizardForm

# TODO: Consider replacing with ModelForm?
# TODO: This is still a mess
from apps.utils.ajax import ajax_error

class Wizard(object):
    """Handles validation and processing of CAMPAIGN creation.

    What looks like a controller actually includes Views.
    """
    def __init__(self, *args, **kwargs):
        #TODO: Error handling
        self.preview    = kwargs.get('preview', False)
        self.request    = kwargs.get('request')
        self.store      = kwargs.get('store')
        self.campaign   = kwargs.get('campaign')
        self.form_cls   = kwargs.get('form')
        self.block_type = kwargs.get('block_type')

    def _is_editing(self):
        # Normally would just return self.campaign, but that seems strange.
        # Favouring explicit vs implicit
        return bool(self.campaign)

    def process(self):
        if self.request.method == 'POST':
            form, response = self._post()
        else:
            form, response = self._get()

        if response:
            return response

        if not self.preview:
            path = 'pinpoint/wizards/%s/ui.html' % self.block_type.slug
            return render_to_response(path, {
                "store": self.store,
                "block_type": self.block_type,
                "block_types": BlockType.objects.all(),
                "products": self.store.product_set.all(),
                "form": form,
                "campaign": self.campaign,
            }, context_instance=RequestContext(self.request))
        else:
            return ajax_error()

    def _get(self):
        if self._is_editing():
            form = self.form_cls(self._get_initial_form_data())
        else:
            form = self.form_cls()

        return form, None

    def _create_form_with_initial_data(self):
        return None

    def _post(self):
        form = self.form_cls(self.request.POST, self.request.FILES)

        if form.is_valid():
            result = self._process_valid_form(form)
            if not self.preview:
                messages.success(self.request, "Your page was saved successfully")

            return None, result

        return form, None

    def _process_valid_form(self, form):
        product = Product.objects.get(id = form.cleaned_data['product_id'])

        if form.cleaned_data['campaign_id']:
            campaign = self._edit_campaign(form, product)

        else:
            campaign = self._create_campaign(form, product)

        campaign.save()

        if not self.preview:
            return HttpResponseRedirect(
                reverse('store-admin', kwargs = {'store_id': self.store.id})
            )
        else:
            response = json.dumps({
                "success": True,
                "url": reverse('campaign', kwargs={
                    'campaign_id': campaign.id
                }),
                "campaign": campaign.id
            })
            return HttpResponse(response, mimetype='application/json')

    def _create_campaign(self, form, product):
        return None

    def _edit_campaign(self, form, product):
        return None


class FeaturedProductWizard(Wizard):
    def _get_initial_form_data(self):
        all_content_blocks = self.campaign.content_blocks.all()

        product_id   = all_content_blocks[0].data.product.id
        product_desc = all_content_blocks[0].data.description

        initial_data = {
            "name"            : self.campaign.name,
            "product_id"      : product_id,
            "page_description": self.campaign.description,
            "description"     : product_desc,
            "campaign_id"     : self.campaign.id,
            }

        product_image = all_content_blocks[0].data.get_image()

        if product_image.__class__.__name__ == "GenericImage":
            initial_data["generic_media_id"] = product_image.id
            initial_data["generic_media_list"] = product_image.get_url() + "\\" + str(product_image.id)

        elif product_image.__class__.__name__ == "ProductMedia":
            initial_data["product_media_id"] = product_image.id

        return initial_data

    def _edit_campaign(self, form, product):
        campaign = Campaign.objects.get(id = form.cleaned_data['campaign_id'])
        campaign.name = form.cleaned_data['name']
        campaign.description = form.cleaned_data.get('page_description', '')

        block_content = self._edit_content_block(campaign, form, product)
        block_content.save()

        if not block_content in campaign.content_blocks.all():
            campaign.content_blocks.clear()
            campaign.content_blocks.add(block_content)

        campaign.live = not self.preview
        return campaign

    def _edit_content_block(self, campaign, form, product):
        block_content = campaign.content_blocks.all()[0]
        block_content.data.product = product
        block_content.data.description = form.cleaned_data['description']

        generic_media_id = form.cleaned_data.get("generic_media_id")
        product_media_id = form.cleaned_data.get("product_media_id")

        has_product_media = product_media_id and\
                            ProductMedia.objects.filter(pk=product_media_id).exists()

        # existing product media was selected
        if has_product_media:
            block_content.data.custom_image = None
            block_content.data.existing_image = ProductMedia.objects.get(
                pk=product_media_id)
            block_content.data.save()

        # an image was uploaded (the form checks that one of these must exist)
        else:
            block_content.data.existing_image = None
            block_content.data.custom_image = GenericImage.objects.get(
                pk=generic_media_id)
            block_content.data.save()

        return block_content


    def _create_campaign(self, form, product):
        block = self._create_content_block(form, product)
        block.save()

        campaign = Campaign(
            store = self.store,
            name = form.cleaned_data['name'],
            description = form.cleaned_data.get('page_description', ''),
            live = not self.preview
        )
        campaign.save()

        campaign.content_blocks.add(block)
        return campaign

    def _create_content_block(self, form, product):
        generic_media_id = form.cleaned_data.get("generic_media_id")
        product_media_id = form.cleaned_data.get("product_media_id")

        has_product_media = product_media_id and\
                            ProductMedia.objects.filter(pk=product_media_id).exists()

        featured_product_data = FeaturedProductBlock(
            product = product,
            description = form.cleaned_data['description']
        )

        # existing product media was selected
        if has_product_media:
            featured_product_data.existing_image = ProductMedia.objects.get(
                pk=product_media_id)
        # an image was uploaded (the form checks that one of these must exist)
        else:
            featured_product_data.custom_image = GenericImage.objects.get(
                pk=generic_media_id)

        featured_product_data.save()
        block_content = BlockContent(
            block_type = self.block_type,
            content_type = ContentType.objects.get_for_model(FeaturedProductBlock),
            object_id = featured_product_data.id
        )
        return block_content

class ShopTheLookWizard(FeaturedProductWizard):
    """Controller for the "Shop the Look" page style.

    Template locations are specified in Wizard.process.
    """
    def _get_initial_form_data(self):
        data = super(ShopTheLookWizard, self)._get_initial_form_data()

        all_content_blocks = self.campaign.content_blocks.all()

        ls_image = all_content_blocks[0].data.get_ls_image()

        # TODO: Append to generic_media_list
        if ls_image.__class__.__name__ == "GenericImage":
            data["ls_generic_media_id"] = ls_image.id

            image_url  = ls_image.get_url() + "\\" + str(ls_image.id)
            media_list = data.get('generic_media_list', '')
            if media_list and image_url not in media_list:
                data["generic_media_list"] += '|' + image_url
            else:
                data["generic_media_list"] = image_url

        elif ls_image.__class__.__name__ == "ProductMedia":
            data["ls_product_media_id"] = ls_image.id

        return data

    def _edit_content_block(self, campaign, form, product):
        block_content = super(ShopTheLookWizard, self)._edit_content_block(
            campaign, form, product)

        ls_generic_media_id = form.cleaned_data.get("ls_generic_media_id")
        ls_product_media_id = form.cleaned_data.get("ls_product_media_id")

        has_ls_product_media = ls_product_media_id and\
                            ProductMedia.objects.filter(pk=ls_product_media_id).exists()

        # existing product media was selected
        if has_ls_product_media:
            block_content.data.custom_ls_image = None
            block_content.data.existingls__image = ProductMedia.objects.get(
                pk=ls_product_media_id)
            block_content.data.save()

        # an image was uploaded (the form checks that one of these must exist)
        else:
            block_content.data.existing_ls_image = None
            block_content.data.custom_ls_image = GenericImage.objects.get(
                pk=ls_generic_media_id)
            block_content.data.save()

        return block_content

    def _create_content_block(self, form, product):
        generic_media_id    = form.cleaned_data.get("generic_media_id")
        product_media_id    = form.cleaned_data.get("product_media_id")
        ls_product_media_id = form.cleaned_data.get("ls_product_media_id")
        ls_generic_media_id = form.cleaned_data.get("ls_generic_media_id")

        product_data = ShopTheLookBlock(
            product = product,
            description = form.cleaned_data['description']
        )

        has_product_media = product_media_id and\
                            ProductMedia.objects.filter(pk=product_media_id).exists()

        if has_product_media:
            product_data.existing_image = ProductMedia.objects.get(
                pk=product_media_id)
        else:
            product_data.custom_image = GenericImage.objects.get(
                pk=generic_media_id)

        has_ls_product_media = ls_product_media_id and\
                       ProductMedia.objects.filter(pk=ls_product_media_id).exists()

        if has_ls_product_media:
            product_data.existing_ls_image = ProductMedia.objects.get(
                pk=ls_product_media_id)
        else:
            product_data.custom_ls_image = GenericImage.objects.get(
                pk=ls_generic_media_id)


        product_data.save()
        block_content = BlockContent(
            block_type = self.block_type,
            content_type = ContentType.objects.get_for_model(ShopTheLookBlock),
            object_id = product_data.id
        )
        return block_content


def featured_product_wizard(request, store, block_type, campaign=None):
    wizard = FeaturedProductWizard(**{
        'preview'   : request.is_ajax(),
        'request'   : request,
        'store'     : store,
        'block_type': block_type,
        'campaign'  : campaign,
        'form'      : FeaturedProductWizardForm
    })

    return wizard.process()

def shop_the_look_wizard(request, store, block_type, campaign=None):
    wizard = ShopTheLookWizard(preview=request.is_ajax(),
                               request=request,
                               store=store,
                               block_type=block_type,
                               campaign=campaign,
                               form=ShopTheLookWizardForm)
    return wizard.process()