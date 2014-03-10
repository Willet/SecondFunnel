from django.conf.urls import patterns, url

urlpatterns = patterns('apps.tracking.views',
   url(r'^pixel.png$', 'pixel', name='pixel'),
   url(r'^tracking.js$', 'tracking', name='tracking'),
   # One view for tracking.js, another for pixel

)
