from django import forms

from apps.assets.models import ProductMedia, GenericMedia

class FeaturedProductWizardForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        label="Page Name",
        widget=forms.TextInput()
    )

    product_id = forms.CharField(
        widget=forms.HiddenInput(),
    )

    page_description = forms.CharField(
        required=False,
        label="Page Description",
        widget=forms.Textarea()
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

        if not (generic_media_id and GenericMedia.objects.filter(pk=generic_media_id).exists()) and \
                not (product_media_id and ProductMedia.objects.filter(pk=product_media_id).exists()):
            raise forms.ValidationError("Please either select an existing "
                        "product image or upload a custom one.")

        return cleaned_data
