from django.db import models
from django.contrib.auth.models import User
import jsonfield


# class Campaign(models.Model):
#     title = models.CharField(max_length=128)
#     google_id = models.CharField(max_length=128)
#
#     start_date = models.DateField
#     end_date = models.DateField
#
#     # TODO either implement or delete (depending on how cache experiment goes)
#     timeStamp = models.DateTimeField(verbose_name="The last time this cache of Analytics was updated",
#                                      auto_now=True)
#
#     # responses will be done by dimension.
#     # metrics:
#     #   ga:sessions,ga:bounces, ga:bounceRate,ga:avgSessionDuration,ga:goalCompletionsAll,
#     #   ga:goal1Completions,ga:goal2Completions,ga:goal3Completions
#     dateHour = jsonfield.JSONField(blank=True)
#
#     #   ga:sessions,ga:bounces,ga:bounceRate,
#     #   ga:goal1ConversionRate,ga:goal2ConversionRate,ga:goal3ConversionsRate
#     deviceCategory = jsonfield.JSONField(blank=True)
#
#     #   ga:sessions,ga:bounces, ga:avgSessionDuration, ga:sessions:new,
#     #   ga:goal1Completions,ga:goal2Completions,ga:goal3Completions
#     #   ga:goal1ConversionRate,ga:goal2ConversionRate,ga:goal3ConversionRate
#     source = jsonfield.JSONField(blank=True)
#
#     #   ga:users,ga:sessions
#     userType = jsonfield.JSONField(blank=True)
#
#     def get_response_by_dimension(self, dimension):
#         if dimension == 'dateHour':
#             return self.dateHour
#         elif dimension == 'deviceCategory':
#             return self.deviceCategory
#         elif dimension == 'source':
#             return self.source
#         elif dimension == 'userType':
#             return self.userType
#         return None
#
#
#     def __unicode__(self):
#         name = 'null'
#         try:
#             name = self.title
#         except:
#             print 'please save and give campaign a title'
#         return name


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

    # campaigns = models.ManyToManyField()

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
