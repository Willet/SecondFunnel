from tastypie.test import TestApiClient

# Never store slashed URLs even if it's a folder. We might want to test whether
# our resolver handles slashes correctly, so let the test author decide if a
# slash should or should not be included.
base_url = '/graph/v1'
login_url = base_url + '/user/login/'
logout_url = base_url + '/user/logout/'
restricted_url = base_url + '/store'
# TODO mock store
store_url = base_url + '/store/38'
# TODO mock page
page_url = store_url + '/page/48'
proxy_url = base_url
resource_url = page_url

# TODO fix (could not dump data)
# the following fixture should include test data that we add to the DB for testing
default_fixtures = ['users.json']

test_user = {
    'username': 'test_user_staff',
    'password': 'password'
}

# We will assume gap/gap is a valid user for now as I don't have fixtures yet
# TODO Replace when we have a fixture with test data
valid_login = {'username': test_user['username'], 'password': test_user['password']}

def LoggedInClient(login=valid_login):
    """ Returns a logged-in client """
    client = TestApiClient()
    client.post(login_url, format='json', data=login)
    return client

def slashed(string):
    """ Appends a backslash to a string if it doesn't have one at the end """
    if (string[-1] != '/'):
        string += '/'
    return string

