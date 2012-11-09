from settings import MEDIA_BUNDLES, INSTALLED_APPS

BUNDLE_NAMES = ['MEDIA_BUNDLES']

for app_name in INSTALLED_APPS:
    if app_name.startswith('apps'):
        try:
            app = __import__(app_name + '.media', None, None, BUNDLE_NAMES)
            bundles = app.MEDIA_BUNDLES
            MEDIA_BUNDLES = MEDIA_BUNDLES + bundles
        except Exception, e:
            print e