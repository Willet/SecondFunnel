from scrapy import signals, log
from sys import stdout, stderr
from django.conf import settings

import hipchat

class LogListener(object):
	"""
	Record all logging from spiders.
	LogListener objects pretend to be file objects by implementing a "write" and 
	a "close" method.  They can then be used by ScrapyFileLogObserver.
	"""
	def __init__(self):
		self.str = ""
	def write(self, string):
		self.str += string
	def flush(self):
		pass
	def close(self):
		pass


class Signals(object):
	fake_log = LogListener()
	@classmethod
	def from_crawler(cls, crawler):
		a = cls()
		a.crawler = crawler

		funcs = [func for func in dir(a) if not func.startswith('_') and func != 'from_crawler']
		for func_name in funcs:
			func = getattr(a, func_name)
			if not callable(func): 
				continue

			signal = getattr(signals, func_name)
			if not signal:
				continue
			crawler.signals.connect(func, signal=signal)

		return a

	def engine_started(self):
		log.ScrapyFileLogObserver(self.fake_log, level=log.DEBUG).start()


	def item_scraped(self, item, response, spider):
		# inc_value uses the + operator!  The __add__ method of lists
		# performs list concatenation.
		# The other methods of this class use the long approach because
		# dicts don't have an __add__ method.
		self.crawler.stats.inc_value('new_items' if item['created'] else 'updated_items', [item['url']],[])
		if not item['in_stock']:
			self.crawler.stats.inc_value('out_of_stock', [item['url']], [])


	def item_dropped(self, item, spider, exception):
		dropped_items = self.crawler.stats.get_value('dropped_items', {})

		msg = str(exception).split(':')[0]
		items = dropped_items.get(msg, [])
		items.append('url: {}'.format(item.get('url', "(?)")))
		dropped_items[msg] = items

		self.crawler.stats.set_value('dropped_items', dropped_items)


	def spider_error(self, failure, response, spider):
		errors = self.crawler.stats.get_value('errors', {})

		msg = failure.getErrorMessage()
		items = errors.get(msg, [])
		items.append('url: {}'.format(response.url))
		errors[msg] = items

		self.crawler.stats.set_value('errors', errors)


	def spider_closed(self, spider, reason):
		if settings.ENVIRONMENT == 'dev':
			pass # return


		HIPCHAT_API_TOKEN = "675a844c309ec3227fa9437d022d05"
		room_id = 1003016  # "Scrapy" room
		h = hipchat.HipChat(token=HIPCHAT_API_TOKEN)

		# locals().update(stats.get_stats()) ???

		stats = self.crawler.stats
		errors = stats.get_value('errors', {})
		dropped_items = stats.get_value('dropped_items', {})
		new_items = stats.get_value('new_items', [])
		updated_items = stats.get_value('updated_items', [])
		total_scraped = new_items + updated_items
		out_of_stock = stats.get_value('out_of_stock', [])

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
		
		h.method(
			"rooms/message",
			method="POST",
			parameters={
				"room_id": room_id,
				"from": "scrapy-" + settings.ENVIRONMENT,
				"message": message,
				"message_format": "text",
				"color": color,
				"notify": 1
			}
		)

		# outfile = open("outfile", 'w')
		# outfile.write(self.fake_log.str)
		# outfile.close()

		# from boto.s3.connection import S3Connection
		# from boto.s3.key import Key

		# conn = S3Connection(
		# 	self.crawler.settings.get('AWS_ACCESS_KEY_ID'), 
		# 	self.crawler.settings.get('AWS_SECRET_ACCESS_KEY')
		# )
		# bucket = conn.get_bucket('scrapy.secondfunnel.com')
		
		# key = Key(bucket)
		# key.key = settings.ENVIRONMENT + '/'
		# key.set_contents_as_string(self.fake_log.str)