from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.utils import simplejson as json
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404

import apps.pinpoint.forms as forms
from apps.assets.models import Product, ProductMedia, GenericImage
from apps.pinpoint.models import (BlockType, BlockContent, Campaign,
                                  FeaturedProductBlock, ShopTheLookBlock)

# TODO: Consider replacing with ModelForm?
# TODO: This is still a mess
from apps.utils.ajax import ajax_error


class Wizard(object):
    """
    This defines a base wizard for customizing block types.
    A wizard handles validation and processing of CAMPAIGN creation.
    Specific block type wizards will inherit from this.
    What looks like a controller also includes Views.

    @ivar preview: Whether the wizard is being run to view a preivew page.
    @ivar request: The request for this wizard.
    @ivar store: The store the page is being created for.
    @ivar campaign: The page that is being created.
    @ivar form_cls: The form class to use.
    @ivar block_type: The block type that this wizard is handling.
    """
    def __init__(self, *args, **kwargs):
        """
        Sets various values for the wizard.

        @keyword preview: Whether this is being created for a page preview
        @keyword request: The request for this wizard.
        @keyword store: The store the page is being created for.
        @keyword campaign: The page that has already been created.
        @keyword form: The form class to use.
        @keyword block_type: The type of block being customized.
        """
        #TODO: Error handling
        self.preview = kwargs.get('preview', False)
        self.request = kwargs.get('request')
        self.store = kwargs.get('store')
        self.campaign = kwargs.get('campaign')
        self.form_cls = kwargs.get('form')
        self.block_type = kwargs.get('block_type')

    def _is_editing(self):
        """
        Determines if the wizard is being used to edit an existing page.

        @return: A bool indicating whether the wizard is being used to edit an existing page.
        """
        # Normally would just return self.campaign, but that seems strange.
        # Favouring explicit vs implicit
        return bool(self.campaign)

    def process(self):
        """
        Processes the wizard's form then renders a response.

        @return: An HttpResponse that renders the form.
        """
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
            return ajax_error({'error': "Preview requested."})

    def _get(self):
        """
        Handles get requests by creating a form. Since this only gets called when
        viewing the form, and not processing it, no processing is done.

        @return: A tuple with a form of the type form_cls and None
        """
        if self._is_editing():
            form = self.form_cls(self._get_initial_form_data())
        else:
            form = self.form_cls()

        return form, None

    def _create_form_with_initial_data(self):
        return None

    def _post(self):
        """
        Handles post requests by creating a form using post and files data,
        then attempts to process the form.

        @return: A tuple with a form of the type form_cls if the form wasn't
        processed, and an HttpResponse if the form was processed.
        """
        form = self.form_cls(self.request.POST, self.request.FILES)

        if form.is_valid():
            try:
                result = self._process_valid_form(form)
                if not self.preview:
                    # messages are shown as a function side effect
                    messages.success(self.request, "Your page was saved successfully")

                return None, result
            except ValidationError:
                pass  # use same return line below

        return form, None

    def _process_valid_form(self, form):
        """
        Creates a pinpoint page from the cleaned form data.

        @param form: The form to get cleaned data from.

        @return: If this is for a preview then return a json response indicating success
        or else return a HttpRedirect that redirects to the admin page.
        """
        product = Product.objects.get(id=form.cleaned_data['product_id'])

        if form.cleaned_data['campaign_id']:
            campaign = self._edit_campaign(form, product)

        else:
            campaign = self._create_campaign(form, product)

        campaign.save()

        if not self.preview:
            return HttpResponseRedirect(
                reverse('store-admin', kwargs={'store_id': self.store.id})
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
        """
        Creates a new pinpoint page using form data and a product

        @param form: The form to get data from.
        @param product: The product for the cotnent block.

        @return: A new Campaign object.

        @attention: This should be changed to support blocks that have many products.
        """
        return None

    def _edit_campaign(self, form, product):
        """
        Edits a campaign using form data and a product.

        @param form: The form to get data from.
        @param product: The product for the cotnent block.

        @return: An existing Campaign object.

        @attention: This should be changed to support blocks that have many products.
        """
        return None


class FeaturedProductWizard(Wizard):
    """Wizard for customizing a featured product block"""
    def _get_initial_form_data(self):
        all_content_blocks = self.campaign.content_blocks.all()

        product_id = all_content_blocks[0].data.product.id
        product_desc = all_content_blocks[0].data.description

        initial_data = {
            "name": self.campaign.name,
            "product_id": product_id,
            "page_description": self.campaign.description,
            "description": product_desc,
            "campaign_id": self.campaign.id,
        }

        product_image = all_content_blocks[0].data.get_image()
        initial_data["product_media_id"] = product_image.id
        initial_data["product_media_list"] = ""

        return initial_data

    def _edit_campaign(self, form, product):
        campaign = Campaign.objects.get(id=form.cleaned_data['campaign_id'])
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

        product_media_id = form.cleaned_data.get("product_media_id")

        block_content.data.custom_image = None
        block_content.data.existing_image = ProductMedia.objects.get(pk=product_media_id)
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
        product_media_id = form.cleaned_data.get("product_media_id")

        featured_product_data = FeaturedProductBlock(
            product = product,
            description = form.cleaned_data['description']
        )

        featured_product_data.existing_image = ProductMedia.objects.get(pk=product_media_id)
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
        data["ls_product_media_id"] = ls_image.id

        return data

    def _edit_content_block(self, campaign, form, product):
        block_content = super(ShopTheLookWizard, self)._edit_content_block(
            campaign, form, product)

        ls_product_media_id = form.cleaned_data.get("ls_product_media_id")

        block_content.data.custom_ls_image = None
        block_content.data.existing_ls_image = ProductMedia.objects.get(
            pk=ls_product_media_id)
        block_content.data.save()

        return block_content

    def _create_content_block(self, form, product):
        product_media_id = form.cleaned_data.get("product_media_id")
        ls_product_media_id = form.cleaned_data.get("ls_product_media_id")

        product_data = ShopTheLookBlock(
            product = product,
            description = form.cleaned_data['description']
        )

        product_data.existing_image = ProductMedia.objects.get(
            pk=product_media_id)
        product_data.existing_ls_image = ProductMedia.objects.get(
            pk=ls_product_media_id)
        
        product_data.save()  # will raise exception if images are missing
        block_content = BlockContent(
            block_type = self.block_type,
            content_type = ContentType.objects.get_for_model(ShopTheLookBlock),
            object_id = product_data.id
        )

        return block_content


def wizard_handler(request, handler, store, block_type, campaign=None):
    """
    A generic wizard handler that passes the request to the appropriate Wizard
    anad Wizard forms based on the handler type that was specified by the calling
    function.

    @param request: The request for the Wizard
    @param handler: The type of Wizard to call
    @param store: The store the page is being created for.
    @param block_type: The featured product block type object.
    @param campaign: Either None if the page is being created or the page being edited.

    @return: An HttpResponse that renders a wizard for customizing a block.
    """
    wizard = None
    handler = "".join([text.title() for text in handler.split("_")])

    try:
        wizard = globals()[handler]
        wizard_form = getattr(forms, handler + "Form")
        wizard = wizard(**{
            'preview': request.is_ajax(),
            'request': request,
            'store': store,
            'block_type': block_type,
            'campaign': campaign,
            'form': wizard_form
        })
    except AttributeError:
        raise Exception("Matching wizard not found, either %s or %s is missing."%(handler, handler + "Form"))

    return wizard.process()
