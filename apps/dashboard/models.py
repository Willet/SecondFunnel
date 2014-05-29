from django.db import models
from django.contrib.auth.models import User
from oauth2client.django_orm import CredentialsField
from south.modelsinspector import add_introspection_rules
import jsonfield

add_introspection_rules([], ["^oauth2client\.django_orm\.CredentialsField"])


class DashBoard(models.Model):
    """
    The analytics information for a given site.
    Each metric is a JSON file containing the response from a
    query to the Google Analytics for the given site with respect to certain dimensions
    """
    site = models.CharField(max_length=128)  # human name for the site that these statistics correspond to
    # prepend with 'ga:' this is the table id that GA uses to refer to the site
    table_id = models.IntegerField(help_text="The number that refers to this customers analytics data")

    timeStamp = models.DateTimeField(verbose_name="The last time this cache of Analytics was updated",
                                     auto_now=True)

    # the quicklook graph on the dashboard page.
    quicklook_total = jsonfield.JSONField(default={}, blank=True)
    quicklook_today = jsonfield.JSONField(default={}, blank=True)


class CredentialsModel(models.Model):
    """
    For storing and retrieving Google credentials
    """
    id = models.ForeignKey(User, primary_key=True)
    credential = CredentialsField()
