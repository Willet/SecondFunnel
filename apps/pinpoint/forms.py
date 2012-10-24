from django import forms

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

    product_image = forms.FileField(
        required=False
    )

    def clean(self):
        """Ensure that either custom or existing image is selected"""

        cleaned_data = super(FeaturedProductWizardForm, self).clean()

        product_image = cleaned_data.get("product_image")
        product_media_id = cleaned_data.get("product_media_id")

        if not product_image and not product_media_id:
            raise forms.ValidationError("Please either select an existing "
                        "product image or upload a custom one.")

        return cleaned_data
