from django.conf import settings
from apps.utils.broadcast import slack

def dump_stats(stats, spider, reason, s3_urls):
    """
    Assemble stats into a brief message, then
    print it to the Scrapy room in Slack.
    @stats scrapy Stats Collection object, as a dict
    @spider spider which was crawling
    @reason why/how the spider was closed, especially whether it was 
    force-shutdown by ctrl-C
    @s3_urls links to s3 showing more details about scrape
    """

    keys = [
        ('errors', 'error'),
        ('items dropped', 'warn'),
        ('items out of stock', 'warn'),
        ('new items', 'info'),
        ('items updated', 'info')
    ]
    stats_collection = {key: stats.get('logging/' + key) or [] for key, _ in keys}

    total = float(sum(map(len, stats_collection.values())))

    result_codes = {
        "shutdown": "Spider {} squashed like a bug (ctrl-C)",
        "finished": "Ran spider {}"
    }
    unknown_result_msg = "Spider {} died with unknown exit condition.  Investigate!"
    title = result_codes.get(reason, unknown_result_msg).format(spider.name.upper())

    level = False if reason == 'finished' else 'error'
    report = []

    for key, lev in keys:
        val = stats_collection[key]
        if val:
            report.append('{} {} ({}%)'.format(len(val), key, int(len(val)*100/total)))
            level = level or lev
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
        level=(level or 'error'),
    )
