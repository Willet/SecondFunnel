from django.conf.urls.defaults import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns('apps.website.urls',
    url(
        r'^(index.html)?$',
        TemplateView.as_view(template_name="index.html"),
        name='website-index'
    ),
    url(
        r'^about(.html)?$',
        TemplateView.as_view(template_name="about.html"),
        name='website-about'
    ),
    url(
        r'^contact(.html)?$',
        TemplateView.as_view(template_name="contact.html"),
        name='website-contact'
    ),
    url(
        r'^why(.html)?$',
        TemplateView.as_view(template_name="why.html"),
        name='website-why'
    ),
)