from django.conf.urls.defaults import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns('apps.website.urls',
    url(
        r'^$',
        TemplateView.as_view(template_name="website/index.html"),
        name='website-index'
    ),
    url(
        r'^about$',
        TemplateView.as_view(template_name="website/about.html"),
        name='website-about'
    ),
    url(
        r'^contact$',
        TemplateView.as_view(template_name="website/contact.html"),
        name='website-contact'
    ),
    url(
        r'^why$',
        TemplateView.as_view(template_name="website/why.html"),
        name='website-why'
    ),
)