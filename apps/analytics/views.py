from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Context


def embedded_analytics(request, app_slug):
    return render_to_response('analytics/pinpoint_embed.html', {
        "app_slug": app_slug
    }, context_instance=RequestContext(request))
