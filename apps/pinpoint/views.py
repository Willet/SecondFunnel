from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse

from apps.pinpoint.models import Campaign

class Product(object):
    url = "www.google.ca"
    title = "Product Name"
    desc = ["Dummy description"]
    price = "$3.50"
    img = ["http://dev.willet-tniechciol.appspot.com/static/pinpointPreview.png"]

def campaign(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    products = []
    for i in range(100):
        products.append(Product())

    return render_to_response('pinpoint/campaign.html', {
        "campaign": campaign,
        "columns": range(4),
        "featured": Product()
    }, context_instance=RequestContext(request))

def pinpoint_admin(request, campaign_id):
    return render_to_response('pinpoint/admin.html', {
        "storeUrl": campaign_id,
        "pageNames": [],
        "pages": [],
        "pageDomain": "/"
    }, context_instance=RequestContext(request))
