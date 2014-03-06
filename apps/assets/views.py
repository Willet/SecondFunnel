from django.core.management import call_command


def import_from_cg(request, store_id, *args):
    """Trigger import remotely.

    :param store_id e.g. 38
    :param *args    e.g. false, content, products, ... (see actual function)
    """
    call_command('importer', store_id, *args, **request.GET)
