import time, os

THEMES_PATH = '/Users/grisha/Code/SecondFunnel-Themes'

THEME_FIELDS = ['page', 'shop_the_look', 'featured_product', 'product',
    'combobox', 'youtube', 'instagram', 'product_preview', 'combobox_preview',
    'instagram_preview', 'instagram_product_preview']

THEMES = [(9, 'NewEggMobile'), (8, 'NewEgg')]

def run():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'secondfunnel.settings.dev'

    from apps.pinpoint.models import StoreTheme

    while True:
        for theme_id, theme_name in THEMES:
            st = StoreTheme.objects.get(id=theme_id)
            for field in THEME_FIELDS:
                file_name = field.replace("_", "-")
                path = '{0}/{1}/{2}.html'.format(
                    THEMES_PATH, theme_name, file_name)

                with open(path, 'r') as source:
                    data = source.read()
                    current_source = st.__getattribute__(field)
                    if current_source != data:
                        print "{0} field changed: {1}".format(theme_name, field)
                        st.__setattr__(field, data)
                        st.save()

        time.sleep(2)

if __name__ == "__main__":
    run()
