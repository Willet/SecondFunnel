from django.conf import settings
from tastypie.paginator import Paginator


class ContentGraphPaginator(Paginator):
    def __init__(self, *args, **kwargs):
        kwargs.pop('collection_name')
        super(ContentGraphPaginator, self).__init__(*args, **kwargs)

    def get_limit(self):
        """Changes the 'results' (CG) param to 'limit'"""

        limit = self.request_data.get('results', 20)
        if limit is None:
            limit = getattr(settings, 'API_LIMIT_PER_PAGE', 20)

        try:
            limit = int(limit)
        except ValueError:
            pass  # superclass handles it

        self.request_data['limit'] = limit

        return super(ContentGraphPaginator, self).get_limit()

    def page(self):
        output = super(ContentGraphPaginator, self).page()

        output['results'] = output['objects']

        meta = output['meta']
        output['meta'] = {
            'cursors': {
                # no previous offset was provided by CG
                'next': meta['offset'] + len(output['results'])
            }
        }

        return output
