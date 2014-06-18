"""
This is essentially urls.py for the scraper app.
"""

from django.conf.urls import patterns, url

from apps.scraper.views import ScrapeNowView

urlpatterns = patterns('apps.scraper.views',
    # regenerate == generate
    url(r'^/?$', ScrapeNowView.as_view()),
)
