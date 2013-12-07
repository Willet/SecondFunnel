from django.http import HttpResponse
from intentrank.mock_tile import mock_tile
from intentrank.get_results import get_results
import json


def get_results_view(request):

    result_count = int(request.GET.get('results')) # Like IR, throws error if not provided
    host = request.META.get('HTTP_HOST')

    results = get_results(host,result_count)

    response = HttpResponse(content=json.dumps(results), status='200')

    return response


def tile_view(request, id):

    host = request.META.get('HTTP_HOST')
    tile = mock_tile(id, host)

    response = HttpResponse(content=json.dumps(tile), status=200)

    return response


