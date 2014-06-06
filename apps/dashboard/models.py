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

    quicklook_total = jsonfield.JSONField(default={}, blank=True)
    quicklook_today = jsonfield.JSONField(default={}, blank=True)

    timeStamp = models.DateTimeField(verbose_name="The last time this cache of Analytics was updated",
                                     auto_now=True)
    # Whether or not this dashboard has reached its daily quota
    # over_quota = models.BooleanField(default=False)

    def __unicode__(self):
        name = 'null'
        try:
            name = self.site_name
        except:
            print 'no site, please save object with a site'
        return name


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    dashboards = models.ManyToManyField(DashBoard)

    def __unicode__(self):
        username = "null"
        try:
            username = self.user.username
        except:
            print 'self.user.username caused an exception. Is there a user?'
        return username
