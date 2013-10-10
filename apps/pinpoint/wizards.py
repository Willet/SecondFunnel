from django.contrib import messages
from django.utils import simplejson as json
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse

from apps.assets.models import Product
from apps.pinpoint.models import BlockType

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