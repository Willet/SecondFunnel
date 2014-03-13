from django.conf import settings
from tastypie.exceptions import BadRequest
from tastypie.paginator import Paginator


class ContentGraphPaginator(Paginator):
    def __init__(self, *args, **kwargs):
        kwargs.pop('collection_name')
        super(ContentGraphPaginator, self).__init__(*args, **kwargs)

    def get_limit(self):
        """Changes the 'results' (CG) param to 'limit'"""
        limit = self.request_data.get('results', self.request_data.get(
            'limit', self.limit))
        if limit is None:
            limit = getattr(settings, 'API_LIMIT_PER_PAGE', 20)

        try:
            limit = int(limit)
        except ValueError:
            raise BadRequest("Invalid limit '%s' provided. Please provide a positive integer." % limit)

        if limit < 0:
            raise BadRequest("Invalid limit '%s' provided. Please provide a positive integer >= 0." % limit)

        if self.max_limit and (not limit or limit > self.max_limit):
            # If it's more than the max, we're only going to return the max.
            # This is to prevent excessive DB (or other) load.
            return self.max_limit

        return limit

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
