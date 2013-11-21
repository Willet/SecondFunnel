import re


def configure_mock_request(mock_request, returns):
    # http://www.voidspace.org.uk/python/mock/examples.html#multiple-calls-with-different-effects
    def response(url, method, body, headers):
        for key, value in returns.iteritems():
            if re.search(key, url):
                return value

        return (None, None)

    mock_request.side_effect = response

    return mock_request