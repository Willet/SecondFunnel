from django.conf import settings
from apps.utils import hipchat_broadcast as hipchat

def dump_stats(stats, spider, reason, s3_urls):
    """
    Assemble stats into a brief message, then
    print it to the Scrapy room in hipchat.
    @stats scrapy Stats Collection object, as a dict
    @spider spider which was crawling
    @reason why/how the spider was closed, especially whether it was 
    force-shutdown by ctrl-C
    @s3_urls links to s3 showing more details about scrape
    """

    keys = [
        ('errors', 'red'),
        ('items dropped', 'yellow'),
        ('items out of stock', 'yellow'),
        ('new items', 'green'),
        ('items updated', 'green')
    ]
    stats_collection = {key: stats.get('logging/' + key) or [] for key, _ in keys}

    total = float(sum(map(len, stats_collection.values())))

    result_codes = {
        "shutdown": "Spider {} squashed like a bug (ctrl-C).  ",
        "finished": "Ran spider {}!  "
    }
    unknown_result_msg = "Spider {} died with unknown exit condition.  Investigate!  "
    message = result_codes.get(reason, unknown_result_msg).format(spider.name.upper())

    color = '' if reason == 'finished' else 'red'
    report = []

    for key, col in keys:
        val = stats_collection[key]
        if val:
            report.append('{} {} ({}%)'.format(len(val), key, int(len(val)*100/total)))
            color = color or col
    report.append('{} total items scraped'.format(int(total)))

    color = color or 'red'

    message += ', '.join([a for a in report if a])
    message += ' (<a href=http://{}>report</a>)(<a href=http://{}>full log</a>)'.format(*s3_urls)

    # apparently 'scrapy-production' is too long for hipchat to handle
    env = "prod" if settings.ENVIRONMENT == "production" else settings.ENVIRONMENT

    hipchat.msg(
        sender='scrapy-' + env,
        room='scrapy',
        message=message,
        type='html',
        color=color,
        notify=1
    )
