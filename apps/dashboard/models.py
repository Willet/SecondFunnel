from django.db import models
from django.contrib.auth.models import User
import jsonfield


class DashBoard(models.Model):
    """
    The analytics information for a given site.
    Each metric is a JSON file containing the response from a
    query to the Google Analytics for the given site with respect to certain dimensions
    """
    # human name for the site that these statistics correspond to
    site_name = models.CharField(max_length=128)
    # prepend with 'ga:' this is the table id that GA uses to refer to the site
    table_id = models.IntegerField(help_text="The number that refers to this customers analytics data")

    # stuff below here isn't used right now
    # TODO either implement or delete (depending on how cache experiment goes)
    timeStamp = models.DateTimeField(verbose_name="The last time this cache of Analytics was updated",
                                     auto_now=True)

    # the quicklook graph on the dashboard page.
    quicklook_total = jsonfield.JSONField(default={}, blank=True)
    quicklook_today = jsonfield.JSONField(default={}, blank=True)

    # # responses will be done by dimension.
    # # metrics:
    # #   ga:sessions,ga:bounces
    # nthMinute = jsonfield.JSONField(blank=True)
    # #   ga:sessions,ga:bounces,ga:avgSessionDuration,ga:goalCompletionsAll,
    # #   ga:goal1Completions,ga:goal2Completions,ga:goal3Completions
    # dateHour = jsonfield.JSONField(blank=True)
    # #   ga:sessions,ga:bounces,ga:bounceRate,ga:goalConversionRateAll,
    # #   ga:goal1Completions,ga:goal2Completions,ga:goal3Completions
    # deviceCategory = jsonfield.JSONField(blank=True)
    # #   ga:sessions,ga:bounces,
    # #   ga:goal1Completions,ga:goal2Completions,ga:goal3Completions
    # source = jsonfield.JSONField(blank=True)
    #
    # # Whether or not this dashboard has reached its daily quota
    # over_quota = models.BooleanField(default=False)

    def __unicode__(self):
        return self.site


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    dashboards = models.ManyToManyField(DashBoard)

    def __unicode__(self):
        return self.user.username