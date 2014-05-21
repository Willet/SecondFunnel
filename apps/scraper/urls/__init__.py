"""
This is essentially urls.py for the scraper app.
"""

from django.conf.urls import patterns, url

# url prefix: /static_pages/
from apps.scraper.views import ScrapeNowView

urlpatterns = patterns('apps.scraper.views',
    # regenerate == generate
    url(r'^/?$', ScrapeNowView.as_view()),
)