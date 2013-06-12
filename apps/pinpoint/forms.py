from django import forms

from apps.assets.models import ProductMedia, GenericImage


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
