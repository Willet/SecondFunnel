from tastypie.paginator import Paginator


class ContentGraphPaginator(Paginator):
    def __init__(self, *args, **kwargs):
        kwargs.pop('collection_name')
        super(ContentGraphPaginator, self).__init__(collection_name='results',
                                                    *args, **kwargs)

    def page(self):
        output = super(ContentGraphPaginator, self).page()

        # First keep a reference.
        output['pagination'] = output['meta']
        # output['results'] = output['objects']

        # Now nuke the original keys.
        del output['meta']
        # del output['objects']

        return output
