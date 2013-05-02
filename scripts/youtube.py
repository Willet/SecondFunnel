"""
Given the username of a channel, pull in all youtube videos in that channel.

If provided, also associate with the listed category
"""
import json
from urllib import urlencode, urlopen
from apps.assets.models import YoutubeVideo


def user_content_generator(username, get_params=None):
    if not get_params:
        get_params = {}

    base_url = 'https://gdata.youtube.com/feeds/api/videos'

    get_params.update({
        'author': username,
        'alt': 'json'
    })

    while True:
        enc_params = urlencode(get_params)
        url = '{0}?{1}'.format(base_url, enc_params)

        results_str = urlopen(url).read()

        results = json.loads(results_str)

        entries = results['feed'].get('entry')

        if not entries:
            return

        for entry in entries:
            yield entry

        start_index = int(results['feed']['openSearch$startIndex']['$t'])
        items = int(results['feed']['openSearch$itemsPerPage']['$t'])

        get_params.update({
            'start-index': start_index + items
        })

def import_from_user(username, store_id, category_ids=None, **kwargs):
    if not category_ids:
        category_ids = []

    if not isinstance(category_ids, list):
        category_ids = [category_ids]

    results = user_content_generator(username, {'max-results': 10})

    ids = [];
    for entry in results:
        for link in entry['link']:
            if link.get('rel') == 'self':
                href = link.get('href')
                id = href.split('/')[-1]
                ids.append(id)

    for id in ids:
        video = YoutubeVideo(video_id=id, store_id=store_id)
        if kwargs.get('dry_run', False):
            print 'Saving video: {0} (categories: {2})'.format(
                id, category_ids
            )
        else:
            video.save()
            for category_id in category_ids:
                video.categories.add(category_id)