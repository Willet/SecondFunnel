from django.shortcuts import render_to_response


def pixel(r):
    pass

def tracking(request):
    return render_to_response('tracking.js', content_type='application/javascript')