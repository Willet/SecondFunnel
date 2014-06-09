from django.conf.urls import patterns, url

urlpatterns = patterns('apps.tracking.views',
   url(r'^conversion\.js$', 'conversion'),
   url(r'^conversion-loader\.js$', 'conversion_loader'),

   # One view for tracking.js, another for pixel
   url(r'^pixel\.gif$', 'pixel', name='pixel'),
   url(r'^(?P<tracking_id>\w+)(?P<dev>-dev)?\.js$', 'tracking', name='tracking'),
)
