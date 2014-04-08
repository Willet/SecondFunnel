from django.template import loader
from django.forms import ModelForm
from django.utils.http import int_to_base36
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.sites.models import get_current_site
from django.core.mail import EmailMessage, get_connection
from django.contrib.auth.tokens import default_token_generator

from apps.assets.models import Category


class HTMLPasswordResetForm(PasswordResetForm):
    # duplicated from django.contrib.auth.forms.PasswordResetForm
    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        """
        Generates a one-use only link for resetting password and sends to the user
        """
        for user in self.users_cache:
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
                }
            subject = loader.render_to_string(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, c)

            # Above is duplicated from PasswordResetForm, unfortunately
            # Replace send_mail call with our call
            HTMLPasswordResetForm.send_mail(subject, email, from_email,
                                            [user.email], content_subtype="html")

    # Duplicated from django.core.mail
    @staticmethod
    def send_mail(subject, message, from_email, recipient_list,
                  fail_silently=False, auth_user=None, auth_password=None,
                  connection=None, content_subtype=None):
        """
        Easy wrapper for sending a single message to a recipient list. All members
        of the recipient list will see the other recipients in the 'To' field.

        If auth_user is None, the EMAIL_HOST_USER setting is used.
        If auth_password is None, the EMAIL_HOST_PASSWORD setting is used.

        Note: The API for this method is frozen. New code wanting to extend the
        functionality should use the EmailMessage class directly.
        """
        connection = connection or get_connection(username=auth_user,
                                                  password=auth_password,
                                                  fail_silently=fail_silently)
        msg = EmailMessage(subject, message, from_email, recipient_list,
                            connection=connection)

        # Our modifications below.
        if content_subtype:
            msg.content_subtype = content_subtype
        return msg.send()


class CategoryForm(ModelForm):
    class Meta:
        model = Category

    def clean(self):
        """
        Validation for a category ensures that we can't add products to a category for which
        the stores do not match.
        """
        store = self.cleaned_data.get('store')
        products = self.cleaned_data.get('products')

        if products:
            for p in products.all():
                if not p.store == store:
                    raise ValidationError("Products in category must have same store as category.")

        return self.cleaned_data
