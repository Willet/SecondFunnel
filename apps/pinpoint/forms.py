import re

from django import forms
from django.forms import ModelForm
from django.core.exceptions import ObjectDoesNotExist

from apps.assets.models import ProductMedia, Product, GenericImage, Store
from apps.pinpoint.models import StoreTheme, Campaign

class FeaturedProductWizardForm(forms.Form):
    """
    Defines the form for configuring a featured product block.

    @ivar name: The name of the pinpoint page.
    @ivar product_id: The id of the selected product to feature.
    @ivar page_changed: Hidden from the user. Keeps track of
        whether the page has changed when the form returns errors.
    @ivar description: The description to override the default
        product's description.
    @ivar product_media_id: Hidden from the user. Keeps track of
        the image id of the selected product media.
    @ivar product_media_list: List of product_media urls and ids
        that were uploaded.  Used to turn GenericImages into ProductMedia
        when creating a campaign.
    @ivar campaign_id: Hidden from the user. Keeps track of the id
        of the page being edited.
    """
    name = forms.CharField(
        max_length=255,
        label="Page Name",
        widget=forms.TextInput()
    )

    product_id = forms.CharField(
        widget=forms.HiddenInput(),
    )

    page_changed = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    description = forms.CharField(
        label="Product Description",
        widget=forms.Textarea()
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

    def clean(self):
        """Ensure that either custom or existing image is selected"""
        cleaned_data = super(FeaturedProductWizardForm, self).clean()

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
        # Either the selected product is a GenericImage or it's a ProductMedia
        # We convert GenericImages to ProductMedia later on, so it is fine
        if product_media_id:
            product_media_id = ProductMedia.objects.filter(pk=product_media_id).exists()

        if not product_media_id:
            raise forms.ValidationError("This field is required.")

        return cleaned_data


class ShopTheLookWizardForm(FeaturedProductWizardForm):
    """
    Defines the form for configuring a shop the look block.

    @ivar ls_product_media_id: Hidden from the user. Keeps track of
        the image id of the selected ls image.
    """
    ls_product_media_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def clean(self):
        """Ensure that a look image was selected."""
        cleaned_data = super(ShopTheLookWizardForm, self).clean()

        ls_product_media_id = cleaned_data.get("ls_product_media_id")

        if ls_product_media_id:
            ls_product_media_id = ProductMedia.objects.filter(pk=ls_product_media_id).exists()

        if not ls_product_media_id:
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
