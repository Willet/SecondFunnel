from django.conf import settings

from apps.utils.broadcast import slack
from apps.utils.classes import ComparableString
from apps.utils.functional import flatten


ERROR = ComparableString(string='error', weight=40)
WARNING = ComparableString(string='warn', weight=30)
INFO = ComparableString(string='info', weight=20)


def dump_stats(stats, spider, reason, s3_urls):
    """
    Assemble stats into a brief message, then
    print it to the Scrapy room in Slack.
    @stats scrapy Stats Collection object, as a dict
    @spider spider which was crawling
    @reason why/how the spider was closed, especially whether it was force-shutdown by ctrl-C
    @s3_urls [summary report url, full log url] s3 links with more scrape details
    """

    keys = [
        # (stats key, slack notification level)
        ('errors', ERROR),
        ('items dropped', WARNING),
        ('items out of stock', WARNING),
        ('new items', INFO),
        ('items updated', INFO)
    ]
    stats_collection = { key: stats.get('logging/' + key) for key, _ in keys }
    
    # items dropped & errors are collections of reasons & urls - flatten it
    stats_collection['errors'] = flatten(stats_collection['errors'].values())
    stats_collection['items dropped'] = flatten(stats_collection['items dropped'].values())

    total = float(sum(map(len, stats_collection.values()))) # float for division operation below

    result_codes = {
        "shutdown": "Spider {0} squashed like a bug (ctrl-C)",
        "finished": "Ran spider {0} for {1}"
    }
    unknown_result_msg = "Spider {} died with unknown exit condition.  Investigate!"
    title = result_codes.get(reason, unknown_result_msg).format(
        spider.name.upper(), getattr(spider, 'reporting_name', '- unspecified -'))

    level = INFO if reason == 'finished' else ERROR
    report = []

    # Build one-line status report, example:
    # "17 items dropped (6%), 4 items out of stock (1%), 246 items updated (92%), 267 total items scraped"
    for key, lev in keys:
        val = stats_collection[key]
        if val:
            report.append('{} {} ({}%)'.format(len(val), key, int(len(val)*100/total)))
            # Update to highest level
            if lev > level:
                level = lev
    report.append('{} total items scraped'.format(int(total)))

    message = ', '.join([a for a in report if a])
    message += '\n<http://{}|report> | <http://{}|full log>'.format(*s3_urls)

    if settings.ENVIRONMENT == 'dev' and getattr(settings,'SLACK_USERNAME', False):
        channel = '@{}'.format(settings.SLACK_USERNAME)
    else:
        channel="#scraper"

    slack.msg(
        channel=channel,
        sender='scrapy-{}'.format(settings.ENVIRONMENT),
        title=title,
        message=message,
        level=unicode(level),
    )
