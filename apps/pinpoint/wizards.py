from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.utils import simplejson as json
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView

import apps.pinpoint.forms as forms
from apps.assets.models import Product, ProductMedia, GenericImage, Store
from apps.pinpoint.models import (BlockType, BlockContent, Campaign,
                                  FeaturedProductBlock, ShopTheLookBlock)
from apps.utils.ajax import ajax_success, ajax_error


class CampaignViewMixin(object):
    """Generic Campaign Mixin.  Allows us to use the Campaign ModelForm to edit Campaigns
    for the various ProductBlock types.
    """
    def __dispatch__(self, *args, **kwargs):
        """Sets the variables to be used by the instance.  Since this is a Class-based view, this
        has to be done under dispatch, rather than __init__.

        @return: None
        """
        self.store = get_object_or_404(Store, pk=kwargs.get('store_id'))
        self.campaign = (None if not kwargs.get('campaign_id', None) else \
                                       get_object_or_404(Campaign, pk=kwargs.get('campaign_id')))
        self.block_type = (get_object_or_404(BlockType, pk=kwargs.get('block_type_id')) if kwargs.get('block_type_id', None) else \
                               self.campaign.content_blocks.all()[0].block_type)

        self.context_data = {
            'store': self.store,
            'block_type': self.block_type,
            'block_types': BlockType.objects.all(),
            'products': self.store.product_set.all(),
            'campaign': self.campaign
        }

        handler = "".join([text.title() for text in self.block_type.handler.split("_")])
        self.form_class = getattr(forms, handler + "Form")
        self.template_name = 'pinpoint/wizards/%s/ui.html' % self.block_type.slug
        self.success_url = reverse('store-admin', kwargs={'store_id': self.store.id})

    def get_initial(self):
        """Returns the initial data to render the form with.

        @return: dict
        """
        if not self.campaign:
            return {}

        campaign = self.campaign
        all_content_blocks = campaign.content_blocks.all()

        product_id = all_content_blocks[0].data.product.id
        product_desc = all_content_blocks[0].data.description

        initial_data = {
            "name": campaign.name,
            "product_id": product_id,
            "page_description": campaign.description,
            "description": product_desc,
            "campaign_id": self.campaign.id
        }

        initial_data["product_media_id"] = all_content_blocks[0].data.get_image().id
        initial_data["product_media_list"] = ""

        # TODO: Is there a better way?
        if self.block_type.name == 'Shop The Look':
            initial_data["ls_product_media_id"] = all_content_blocks[0].data.get_ls_image().id
        
        return initial_data

    def preview_or_response(self, request, response):
        """Returns a json response for generating a preview if the request is an ajax request, otherwise
        it processes the form and either creates a model if validation succeeded or returns the form
        with errors.

        @param request: The request object.
        @param response: A function to generate the response
        @return: HttpResponse
        """
        if request.is_ajax():
            # Don't want to save the object, rather use the passed data to formulate
            # a response
            # TODO: How do?
            return ajax_error()

        self.request = request
        return response()

    def form_valid(self, form):
        """If the form is valid, saves the form and redirects successfully.

        @param form: ModelForm
        @return: HttpResponse
        """
        self.object = form.save(**self.context_data)
        messages.success(self.request, "Your page was saved successfully")

        return HttpResponseRedirect(self.get_success_url())


class CampaignCreateView(CampaignViewMixin, CreateView):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Decorated dispatch to force login_required."""
        self.__dispatch__(*args, **kwargs)
        return super(CampaignCreateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        """Adds key, value pairs to the context dictionary for rendering a response.

        @param kwargs: Dictionary
        @return: Dictionary
        """
        kwargs.update(self.context_data)
        return super(CampaignCreateView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        """Posts the data to the form, if validation succeeds, new models are created and saved
        to the database, otherwise the form is returned with validation errors.

        @param request: The request object.
        @param args: List of arguments.
        @param kwargs: Dictionary of key-value argument pairs.
        @return: HttpResponse
        """
        response = lambda: super(CampaignCreateView, self).post(request, *args, **kwargs)

        return self.preview_or_response(request, response)


class CampaignUpdateView(CampaignViewMixin, UpdateView):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Decorated dispatch to force login_required."""
        self.__dispatch__(*args, **kwargs)
        return super(CampaignUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        """Adds key, value pairs to the context dictionary for rendering a response.

        @param kwargs: Dictionary
        @return: Dictionary
        """
        kwargs.update(self.context_data)
        return super(CampaignUpdateView, self).get_context_data(**kwargs)

    def get_object(self, queryset=None):
        """Returns the object associated with the campaign.

        @param queryset: A set of objects to perform a query on.
        @return: Campaign
        """
        return self.campaign

    def post(self, request, *args, **kwargs):
        """Posts the data to the form, if validation succeeds, new models are created and saved
        to the database, otherwise the form is returned with validation errors.

        @param request: The request object.
        @param args: List of arguments.
        @param kwargs: Dictionary of key-value argument pairs.
        @return: HttpResponse
        """
        response = lambda: super(CampaignUpdateView, self).post(request, *args, **kwargs)

        return self.preview_or_response(request, response)
