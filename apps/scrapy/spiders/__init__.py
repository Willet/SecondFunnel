from scrapy.selector import SelectorList
from apps.scrapy.utils import monkeypatch_method

# MonkeyPatch SelectorList to add useful methods
@monkeypatch_method(SelectorList)
def extract_first(self):
    items = iter(self.extract())
    return next(items, None)
