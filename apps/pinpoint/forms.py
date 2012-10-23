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
