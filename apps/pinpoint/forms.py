from django import forms

class FeaturedProductWizardForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        label="Page Name",
        widget=forms.TextInput(
            attrs={
                'placeholder': ''
            }
        ),
        help_text="Select a name for this PinPoint page for your reference."
    )

    product_id = forms.CharField(
        widget=forms.HiddenInput(),
    )

    description = forms.CharField(
        label="Product Description",
        widget=forms.Textarea(
            attrs={
                'placeholder': '',
                'rows': '5',
                'cols': '0'
            }
        )
    )

    product_media_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    product_image = forms.FileField(
        required=False
    )
