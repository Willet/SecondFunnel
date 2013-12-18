try:
    from concurrent import futures  # Python 2.7+ / builtin
except ImportError:
    import futures  #  Python 2.6 / backport installed by requirements.txt


def parallel_map(function, iterable, max_workers=None, raise_on_exceptions=True,
                 default_value=None):
    """Execute any non-threaded function on a list iterable with as many
    threads as the number of items in iterable, up to 20 (an arbitrary
    limit where threading has diminishing returns).

    Differs from futures.Executor.map() in that this allows default values to
    be set on undefined iterable items.

    Exception handling is the same as map(), where exception caused by
    one item will kill other operations.

    :type function object
    :type iterable list

    Example:
    >>> import requests
    >>> urls = ['http://abc.com', 'http://def.org']
    >>> pages = parallel_map(lambda x: requests.get(x).text, urls)
    >>> pages
    ['...', '...']  # contents for each page, ordered

    Iterable cannot be a dict.
    Items in iterable cannot be lists.
    parallel_map can be composed, i.e. parallel_map(parallel_map(...))

    """
    pool = futures.ThreadPoolExecutor
    item_count = len(iterable)
    results = [default_value] * item_count

    if not max_workers:
        max_workers = item_count
    max_workers = min(max_workers, 20)

    with pool(max_workers=max_workers) as executor:
        # dict for storing async arrival of results
        futr = dict((executor.submit(function, item), item) \
                    for item in iterable)

        for future in futures.as_completed(futr):
            key = futr[future]  # retrieve index
            index_of_this_result = iterable.index(key)
            if future.exception() is not None:
                if raise_on_exceptions:
                    raise future.exception()
                else:
                    results[index_of_this_result] = future.exception()
            else:
                results[index_of_this_result] = future.result()

    return results


def parallelize_lambdas(lambdas, max_workers=None, raise_on_exceptions=True,
                        default_value=None):
    """Allows parallel execution of *different* code blocks.

    :param lambdas list  of either functions, or tuple(function, *args)

    :returns list  results from these lambdas where applicable.
    """
    pool = futures.ThreadPoolExecutor
    item_count = len(lambdas)
    results = [default_value] * item_count

    if not max_workers:
        max_workers = item_count
    max_workers = min(max_workers, 20)

    with pool(max_workers=max_workers) as executor:
        futr = {}
        for lbd in lambdas:
            # auto-destructuring of fn and arg tuples
            if type(lbd) == tuple or type(lbd) == list:
                fn, args = lbd[0], lbd[1:]
            else:
                fn, args = lbd, []

            futr[executor.submit(fn, *args)] = lbd

        for future in futures.as_completed(futr):
            key = futr[future]  # retrieve index
            index_of_this_result = lambdas.index(key)
            if future.exception() is not None:
                if raise_on_exceptions:
                    raise future.exception()  # standard map raises
                else:
                    results[index_of_this_result] = future.exception()
            else:
                results[index_of_this_result] = future.result()

    return results
