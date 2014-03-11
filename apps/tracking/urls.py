from django.conf.urls import patterns, url

urlpatterns = patterns('apps.tracking.views',
   url(r'^pixel.gif$', 'pixel', name='pixel'),
   url(r'^(?P<tracking_id>).js$', 'tracking', name='tracking'),
   # One view for tracking.js, another for pixel

)
