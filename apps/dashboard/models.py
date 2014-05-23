__author__ = 'tristanpotter'
from django.db import models
from django.contrib.auth.models import User
from oauth2client.django_orm import FlowField, CredentialsField
import jsonfield


class Site(models.Model):
    """
    The analytics information for a given site.
    Each metric is a JSON file containing the response from a
    query to the Google Analytics for the given site with respect to the dimensions
    ga:dateHour,ga:nthMinute,ga:campaign,ga:source,ga:browser,ga:operatingSystem,ga:deviceCategory,ga:latitude,ga:longitude,
    ga:userAgeBracket,ga:userGender,
    """
    site = models.CharField(max_length=128)  # human name for the site that these statistics correspond to
    # prepend with 'ga:' this is the table id that GA uses to refer to the site
    table_id = models.IntegerField(unique=True)

    pageLoadTime = jsonfield.JSONField  # in milliseconds

    # prepend fields with 'ga:' to get the query name for the metric
    sessions = jsonfield.JSONField()
    sessionDuration = jsonfield.JSONField()
    avgSessionDuration = jsonfield.JSONField()

    bounces = jsonfield.JSONField()
    bounceRate = jsonfield.JSONField()

    goal01Completions = jsonfield.JSONField()
    goal02Completions = jsonfield.JSONField()
    goal03Completions = jsonfield.JSONField()
    goalCompletionsAll = jsonfield.JSONField()

    goal01ConversionRate = jsonfield.JSONField()
    goal02ConversionRate = jsonfield.JSONField()
    goal03ConversionRate = jsonfield.JSONField()
    goalConversionRateAll = jsonfield.JSONField()


class FlowModel(models.Model):
    id = models.ForeignKey(User, primary_key=True)
    flow = FlowField()


class CredentialsModel(models.Model):
    id = models.ForeignKey(User, primary_key=True)
    credential = CredentialsField()