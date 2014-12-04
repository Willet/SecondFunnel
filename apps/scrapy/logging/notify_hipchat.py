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

    errors = stats.get('errors', {})
    dropped_items = stats.get('dropped_items', {})
    new_items = stats.get('new_items', [])
    updated_items = stats.get('updated_items', [])
    total_scraped = new_items + updated_items
    out_of_stock = stats.get('out_of_stock', [])

    result_codes = {
        "shutdown": "Spider {} squashed like a bug (ctrl-C).  ",
        "finished": "Ran spider {}!  " + "But it failed" * bool(errors)
    }
    unknown_result_msg = "Spider {} died with unknown exit condition.  Investigate!"
    message = result_codes.get(reason, unknown_result_msg).format(spider.name.upper())

    color = "" if reason == "finished" else "red"

    report = []
    if errors:
        report.append("{} errors".format(len(errors)))
        color = "red"
    if dropped_items:
        report.append("{} items dropped".format(len(dropped_items)))
        color = color or "yellow"
    if new_items:
        report.append("{} new items".format(len(new_items)))
    if updated_items:
        report.append("{} items updated".format(len(updated_items)))
    report.append("{} total items scraped".format(len(total_scraped)))
    if out_of_stock:
        report.append("{} items out of stock".format(len(out_of_stock)))
        color = color or "yellow"
    color = color or "green"

    message += ', '.join([a for a in report if a])
    message += ' (<a href={}>report</a>)(<a href={}>full log</a>)'.format(*s3_urls)

    hipchat.msg(
        sender='scrapy-' + settings.ENVIRONMENT,
        room='scrapy',
        message=message,
        type='html',
        color=color,
        notify=1
    )
