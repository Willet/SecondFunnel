import re

from scrapy.contracts import ContractsManager
from scrapy.http import Request
from scrapy.linkextractors import _re_type, _matches
from scrapy.selector import SelectorList
from scrapy.spiders import Rule as BaseRule
from scrapy.utils.python import get_spec
from scrapy.utils.misc import arg_to_iter

from apps.scrapy.utils.misc import monkeypatch_method


class Rule(BaseRule):
    """
    Rule is extended to support restricting based on the request url

    allow_sources: <regex> or [<regex>] that return True if source url should apply
    deny_sources: <regex> or [<regex>] that return True if source url should NOT apply
    """
    def __init__(self, *args, **kwargs):
        self.allow_res = [x if isinstance(x, _re_type) else re.compile(x)
                          for x in arg_to_iter(kwargs.pop('allow_sources', None))]

        self.deny_res = [x if isinstance(x, _re_type) else re.compile(x)
                         for x in arg_to_iter(kwargs.pop('deny_sources', None))]

        super(Rule, self).__init__(*args, **kwargs)

    def source_allowed(self, url):
        if self.allow_res and not _matches(url, self.allow_res):
            return False
        if self.deny_res and _matches(url, self.deny_res):
            return False
        return True


# MonkeyPatch SelectorList to add useful methods
@monkeypatch_method(SelectorList)
def extract_first(self):
    items = iter(self.extract())
    return next(items, '')

@monkeypatch_method(SelectorList)
def re_first(self, regex):
    items = iter(self.re(regex))
    return next(items, '')

@monkeypatch_method(ContractsManager)
def from_method(self, method, results):
    """
    Copied from `scrapy.contracts.ContractManager`.
    """
    contracts = self.extract_contracts(method)
    if contracts:
        # calculate request args
        args, kwargs = get_spec(Request.__init__)
        kwargs['callback'] = method
        for contract in contracts:
            kwargs = contract.adjust_request_args(kwargs)

        # create and prepare request
        args.remove('self')
        if set(args).issubset(set(kwargs)):
            # Willet: All that we do is modify these two lines to access the
            # `request_cls` from the spider if it exists.
            req_cls = getattr(method.im_self, 'request_cls', Request)
            request = req_cls(**kwargs)

            # execute pre and post hooks in order
            for contract in reversed(contracts):
                request = contract.add_pre_hook(request, results)
            for contract in contracts:
                request = contract.add_post_hook(request, results)

            return request
