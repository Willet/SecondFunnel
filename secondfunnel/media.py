from settings import MEDIA_BUNDLES, INSTALLED_APPS

BUNDLE_NAME = 'MEDIA_BUNDLES'
BUNDLE_FILE = 'media'

for app_name in INSTALLED_APPS:
    if app_name.startswith('apps'):
        try:
            path = '{app}.{media}'.format(app=app_name, media=BUNDLE_FILE)
            app  = __import__(path, None, None, [BUNDLE_NAME])

            bundles       = getattr(app, BUNDLE_NAME)
            MEDIA_BUNDLES = MEDIA_BUNDLES + bundles
        except Exception, e:
            print e