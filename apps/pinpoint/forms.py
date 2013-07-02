from django import forms
from django.forms import ModelForm

from apps.assets.models import ProductMedia, GenericImage, Store
from apps.pinpoint.models import StoreTheme, Campaign
from apps.utils import safe_getattr


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
        the image id if the user picked an existing product image.
    @ivar generic_media_id: Hidden from the user. Keeps track of
        the iamge id if the user uploaded a new image.
    @ivar generic_media_list: Hidden from the user. Keeps track of
        all uploaded images so they persist when the form returns
        errors.
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

    generic_media_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    generic_media_list = forms.CharField(
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

        generic_media_id = cleaned_data.get("generic_media_id")
        product_media_id = cleaned_data.get("product_media_id")

        generic_media_exists = generic_media_id and GenericImage.objects.filter(pk=generic_media_id).exists()
        product_media_exists = product_media_id and ProductMedia.objects.filter(pk=product_media_id).exists()

        if not generic_media_exists and not product_media_exists:
            raise forms.ValidationError("This field is required.")

        return cleaned_data


class ShopTheLookWizardForm(FeaturedProductWizardForm):
    """
    Defines the form for configuring a shop the look block.

    @ivar ls_product_media_id: Hidden from the user. Keeps track of
        the image id if the user picked an existing product image
        as a lifestyle image.
    @ivar ls_generic_media_id: Hidden from the user. Keeps track of
        the iamge id if the user uploaded a new image as a lifestyle
        image.
    """

    ls_product_media_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    ls_generic_media_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def clean(self):
        """Ensure that either custom or existing image is selected"""

        cleaned_data = super(ShopTheLookWizardForm, self).clean()

        ls_generic_media_id = cleaned_data.get("ls_generic_media_id")
        ls_product_media_id = cleaned_data.get("ls_product_media_id")

        ls_generic_media_exists = ls_generic_media_id and GenericImage\
            .objects.filter(pk=ls_generic_media_id).exists()
        ls_product_media_exists = ls_product_media_id and ProductMedia.objects\
            .filter(pk=ls_product_media_id).exists()

        if not (ls_generic_media_exists or ls_product_media_exists):
            raise forms.ValidationError("You must choose a 'look' image")

        return cleaned_data

class ThemeForm(ModelForm):
    # TODO: How to filter on self?
    # e.g. we only want to choose campaigns, store based on current store.
    store_theme = forms.ModelChoiceField(queryset=Store.objects.none())
    store_mobile_theme = forms.ModelChoiceField(queryset=Store.objects.none())

    campaign_theme = forms.ModelChoiceField(queryset=Campaign.objects.none())
    campaign_mobile_theme = forms.ModelChoiceField(queryset=Campaign.objects.none())

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
            self.fields['store_theme'].initial = safe_getattr(
                self.instance, 'store')
            self.fields['store_mobile_theme'].initial = safe_getattr(
                self.instance, 'store_mobile')
            self.fields['campaign_theme'].initial = safe_getattr(
                self.instance, 'theme')
            self.fields['campaign_mobile_theme'].initial = safe_getattr(
                self.instance, 'mobile')

    class Meta:
        model = StoreTheme
        exclude = ['slug', 'created', 'last_modified']

    def clean(self):
        cleaned_data = super(ThemeForm, self).clean()
        return cleaned_data
