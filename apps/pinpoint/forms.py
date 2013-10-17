from django import forms
from django.forms import ModelForm
from django.core.exceptions import ObjectDoesNotExist

from apps.assets.models import Store
from apps.pinpoint.models import StoreTheme, Campaign


class ThemeForm(ModelForm):
    # TODO: Can we migrate these fields to the theme?
    # Then we wouldn't have to make these elaborate extra fields...
    store_theme = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Store.objects.none()
    )

    campaign_theme = forms.ModelMultipleChoiceField(
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
