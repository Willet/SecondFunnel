__author__ = 'tristanpotter'
from django.db import models
from django.contrib.auth.models import User
from oauth2client.django_orm import CredentialsField
import jsonfield


class DashBoard(models.Model):
    """
    The analytics information for a given site.
    Each metric is a JSON file containing the response from a
    query to the Google Analytics for the given site with respect to the dimensions
    ga:dateHour,ga:nthMinute,
    ga:campaign,ga:source,
    ga:browser,ga:operatingSystem,ga:deviceCategory,
    later :: ga:latitude,ga:longitude
    later :: ga:userAgeBracket,ga:userGender
    """
    site = models.CharField(max_length=128)  # human name for the site that these statistics correspond to
    # prepend with 'ga:' this is the table id that GA uses to refer to the site
    table_id = models.IntegerField(help_text="The number that refers to this customers analytics data")

    timeStamp = models.DateTimeField(verbose_name="The last time this cache of Analytics was updated",
                                     auto_now=True)

    quicklook_total = jsonfield.JSONField(default="{}", blank=True)
    quicklook_today = jsonfield.JSONField(default="{}", blank=True)

    def update(self, ga_data):
        pass


class CredentialsModel(models.Model):
    id = models.ForeignKey(User, primary_key=True)
    credential = CredentialsField()