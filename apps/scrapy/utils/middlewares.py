from scrapy_webdriver.middlewares import WebdriverSpiderMiddleware

class PatientWebdriverSpiderMiddleware(WebdriverSpiderMiddleware):
	"""
	A version of WebdriverSpiderMiddleware which waits 10 seconds
	if elements aren't loading
	"""
	def __init__(self, crawler):
		super(PatientWebdriverSpiderMiddleware, self).__init__(crawler)
		self.manager.webdriver.implicitly_wait(10)