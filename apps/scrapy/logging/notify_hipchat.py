import hipchat
from django.conf import settings

HIPCHAT_API_TOKEN = "675a844c309ec3227fa9437d022d05"
scrapy_room = 1003016  # hipchat room_id
h = hipchat.HipChat(token=HIPCHAT_API_TOKEN)

def dump_stats(stats, spider, reason, s3_stuff):
    """
    Assemble stats into a brief message, then
    print it to the Scrapy room in hipchat.
    TODO: message links to more details (s3).
    @stats scrapy Stats Collection object, as a dict
    @spider spider which was crawling
    @reason why/how the spider was closed, especially whether it was 
    force-shutdown by ctrl-C.
    """

    # locals().update(stats) ???

    errors = stats.get('errors', {})
    dropped_items = stats.get('dropped_items', {})
    new_items = stats.get('new_items', [])
    updated_items = stats.get('updated_items', [])
    total_scraped = new_items + updated_items
    out_of_stock = stats.get('out_of_stock', [])

    report = []
    color = ""

    if errors:
        if reason != "shutdown":
            report.append("But it failed. ")
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

    if reason == "shutdown":
        message = "Spider {} squashed like a bug (ctrl-C).  ".format(spider.name.upper())
        color = "red"
    else:
        message = "Ran spider {}!  ".format(spider.name.upper(), settings.ENVIRONMENT)
    message += ", ".join(report)
    message += ' (<a href={}>report</a>)(<a href={}>full log</a>)'.format(*s3_stuff)

    h.method(
        "rooms/message",
        method="POST",
        parameters={
            "room_id": scrapy_room,
            "from": "scrapy-" + settings.ENVIRONMENT,
            "message": message,
            "message_format": "html",
            "color": color,
            "notify": 1
        }
    )
