from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext


def embedded_analytics(request):
    return render_to_response('analytics/pinpoint_embed.html', {
    }, context_instance=RequestContext(request))
