import re

from django import forms
from django.forms import ModelForm
from django.core.exceptions import ObjectDoesNotExist

from apps.assets.models import ProductMedia, Product, GenericImage, Store
from apps.pinpoint.models import StoreTheme, Campaign, FeaturedProductBlock, ShopTheLookBlock, BlockContent, ContentType


class CampaignForm(ModelForm):
    """Base form used when editing a Pinpoint page (Campaign).

    @ivar product_id: The id of the selected product to feature.
    @ivar product_changed: Hidden from the user.  Keeps track of
        whether the page has changed when the form returns errors.
    @ivar product_media_id: Hidden from the user.  Keeps track of the image
        id of the image to use for the featured block.
    @ivar product_media_list: Hidden from teh user.  Keepst track of all
        upload images so they persist when the form returns errors.
    @ivar campaign_id: Hidden from the user.  Keeps track of the id of
        the page being edited.
    """
    product_id = forms.CharField(
        widget=forms.HiddenInput(),
    )

    page_changed = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    product_media_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    product_media_list = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    campaign_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Campaign
        fields = ['name', 'description']

    def add_additional(self, data):
        """Add any additional attributes to the data being edited.

        @param data: A FeaturedProductBlock or ShopTheLookBlock
        @return: None
        """
        pass

    def clean(self):
        """Ensure that an image was selected for use by the block.  Also
        convert any GenericImages to ProductMedia at this time.

        @return: dict
        """
        cleaned_data = super(CampaignForm, self).clean()

        product_instance = Product.objects.get(pk=cleaned_data.get("product_id"))
        product_media_id = cleaned_data.get("product_media_id")
        media_list = re.findall(r"(?:(.+?)\\(\d+?)(?:\||$))", cleaned_data.get("product_media_list"))

        # Turn any GenericImages into ProductMedia at this point
        # TODO: Is there a better way?
        for media in media_list:
            url, id = media[0], media[1]

            if not GenericImage.objects.filter(pk=id).exists():
                continue

            image = GenericImage.objects.get(pk=id)

            p = ProductMedia(
                product = product_instance
            )
            p.remote = image.remote
            p.hosted = image.hosted
            p.save()
            image.delete()

            if id == product_media_id:
                product_media_id = p.id
                cleaned_data["product_media_id"] = product_media_id

        cleaned_data["product_media_list"] = media_list

        if not product_media_id or not ProductMedia.objects.filter(pk=product_media_id).exists():
            raise forms.ValidationError("This field is required.")

        return cleaned_data


    def get_or_create_block(self, model, product, block_type, product_block = None):
        """Create a ProductBlock for the Campaign instance using
        the cleaned data.

        @param model: The campaign instance
        @param product: The product associated with that campaign.
        @param block_type: The type of ProductBlock.
        @param product_block: The ProductBlock to use for the campaign.
        @return: FeaturedProductBlock or ShopTheLookBlock
        """
        if not product_block:
            pass

        product_media_id = self.cleaned_data.get("product_media_id")
        block_content = None

        if len(model.content_blocks.all()) == 0:
            data = product_block(
                product = product,
                description = self.cleaned_data.get("description", "")
            )
            data.image = ProductMedia.objects.get(pk=product_media_id)
            # Get any additional items for the product block
            self.add_additional(data)
            data.save()
            block_content = BlockContent(
                block_type = block_type,
                content_type = ContentType.objects.get_for_model(product_block),
                object_id = data.id
            )
        else:
            block_content = model.content_blocks.all()[0]
            block_content.data.product = product
            block_content.data.description = self.cleaned_data.get("description", "")
            block_content.data.image = ProductMedia.objects.get(pk=product_media_id)
            self.add_additional(block_content.data)
            block_content.data.save()

        return block_content
                

    def save(self, *args, **kwargs):
        """Saves the campaign instance by first editing/creating the associated product
        block, then using the cleaned data to update the Campaign fields.

        @return: Campaign
        """
        model = None
        if kwargs.get('campaign'):
            model = kwargs.get('campaign')
        elif self.cleaned_data.get('campaign_id'):
            model = Campaign.objects.get(pk=self.cleaned_data.get('campaign_id'))
        else:
            model = Campaign(
                store = kwargs.get('store'),
            )
            model.save()

        product = Product.objects.get(pk=self.cleaned_data.get('product_id'))
        block = self.get_or_create_block(model, product, kwargs.get('block_type'))
        block.save()

        model.name = self.cleaned_data.get('name')
        model.description = self.cleaned_data.get('description', '')

        if not block in model.content_blocks.all():
            model.content_blocks.clear()
            model.content_blocks.add(block)

        model.live = not kwargs.get('preview')
        model.save()

        return model


class FeaturedProductWizardForm(CampaignForm):
    """The WizardForm used to create a Campaign with a FeaturedProductBlock."""
    def get_or_create_block(self, model, product, block_type):
        """Create a ProductBlock for the Campaign instance using
        the cleaned data.

        @param model: The campaign instance
        @param product: The product associated with that campaign.
        @param block_type: The type of ProductBlock.
        @return: FeaturedProductBlock
        """
        return super(FeaturedProductWizardForm, self).get_or_create_block(model, product, block_type, FeaturedProductBlock)


class ShopTheLookWizardForm(CampaignForm):
    """The WizardForm used to create a Campaign with a ShopTheLookBlock.

    @ivar ls_product_media_id: Hidden from the user.  Keeps track of
        the image id to be used as a lifestyle image.
    """
    ls_product_media_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def add_additional(self, data):
        """Add any additional attributes to the data being edited.

        @param data: A FeaturedProductBlock or ShopTheLookBlock
        @return: None
        """
        data.ls_image = ProductMedia.objects.get(pk=self.cleaned_data.get("ls_product_media_id"))
        data.save()

    def get_or_create_block(self, model, product, block_type):
        """Create a ProductBlock for the Campaign instance using
        the cleaned data.

        @param model: The campaign instance
        @param product: The product associated with that campaign.
        @param block_type: The type of ProductBlock.
        @return: ShopTheLookBlock
        """
        return super(ShopTheLookWizardForm, self).get_or_create_block(model, product, block_type, ShopTheLookBlock)

    def clean(self):
        """Ensure that an image was selected for use by the block.  Also
        convert any GenericImages to ProductMedia at this time.

        @return: dict
        """
        cleaned_data = super(ShopTheLookWizardForm, self).clean()

        ls_product_media_id = cleaned_data.get("ls_product_media_id")

        if not ls_product_media_id or not ProductMedia.objects.filter(pk=ls_product_media_id).exists():
            raise forms.ValidationError("You must choose a 'look' image")

        return cleaned_data


class ThemeForm(ModelForm):
    # TODO: Can we migrate these fields to the theme?
    # Then we wouldn't have to make these elaborate extra fields...
    store_theme = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Store.objects.none()
    )

    store_mobile_theme = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Store.objects.none()
    )

    campaign_theme = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Campaign.objects.none()
    )

    campaign_mobile_theme = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Campaign.objects.none()
    )

    FORM_ATTR = {
        'store_theme': 'theme',
        'store_mobile_theme': 'mobile',
        'campaign_theme': 'theme',
        'campaign_mobile_theme': 'mobile'
    }

    THEME_ATTR = {
        'store_theme': 'store',
        'store_mobile_theme': 'store_mobile',
        'campaign_theme': 'theme',
        'campaign_mobile_theme': 'mobile'
    }

    def __init__(self, *args, **kwargs):
        store_id = kwargs.pop('store_id', None)

        super(ThemeForm, self).__init__(*args, **kwargs)

        self.fields['store_theme'].queryset = Store.objects.filter(pk=store_id)
        self.fields['store_mobile_theme'].queryset = Store.objects.filter(
            pk=store_id
        )
        self.fields['campaign_theme'].queryset = Campaign.objects.filter(
            store_id=store_id)
        self.fields['campaign_mobile_theme'].queryset = Campaign.objects\
            .filter(store_id=store_id)

        if self.instance:
            for key, value in self.THEME_ATTR.iteritems():
                try:
                    self.fields[key].initial = list(getattr(
                        self.instance, value
                    ).all())
                except ObjectDoesNotExist as o:
                    self.fields[key].initial = []

    class Meta:
        model = StoreTheme
        exclude = ['slug', 'created', 'last_modified']

    def clean(self):
        c_data = super(ThemeForm, self).clean()

        # Must have at least *one* of the four fields
        associations = [c_data.get(k) for k in self.THEME_ATTR.keys()]

        if not any(associations):
            raise forms.ValidationError(
                "You must assign the theme to one of "
                "'Store Theme', 'Store Mobile Theme' "
                "'Campaign Theme', 'Campaign Mobile Theme'"
            )

        return c_data

    def save(self, *args, **kwargs):
        model = super(ThemeForm, self).save(*args, **kwargs)

        changed_objs = {}
        for key in self.changed_data:
            qs = self.cleaned_data[key]
            initial = self.fields[key].initial

            # If it hasn't changed, continue
            if qs == initial:
                continue

            # Remove any previous associations
            for elem in (initial or []):
                change_id = elem.__class__.__name__ + str(elem.pk)
                elem = changed_objs.get(change_id, elem)
                setattr(elem, self.FORM_ATTR[key], None)
                changed_objs[change_id] = elem

            # Add new associations
            for elem in qs:
                change_id = elem.__class__.__name__ + str(elem.pk)
                elem = changed_objs.get(change_id, elem)
                setattr(elem, self.FORM_ATTR[key], model)
                changed_objs[change_id] = elem

            # ... but if there are none, set association from the 'other side'
            if not qs:
                change_id = model.__class__.__name__ + str(model.pk)
                elem = changed_objs.get(change_id, model)
                setattr(elem, self.THEME_ATTR[key], [])
                changed_objs[change_id] = elem

        for obj in changed_objs.values():
            obj.save()

        return model
