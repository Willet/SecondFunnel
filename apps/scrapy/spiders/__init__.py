from scrapy.contracts import ContractsManager
from scrapy.http import Request
from scrapy.selector import SelectorList
from scrapy.utils.python import get_spec

from apps.scrapy.utils.misc import monkeypatch_method


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
