from tastypie.test import TestApiClient
from . import mocks
from .utils import configure_mock_request

base_url = '/graph/v1'
login_url = base_url + '/user/login/'
logout_url = base_url + '/user/logout/'

restricted_url = base_url + '/store'
store_url = base_url + '/store/38'
page_url = store_url + '/page/48'
proxy_url = base_url
resource_url = page_url

default_fixtures = ['users.json']

test_user = {
    'username': 'test_user_staff',
    'password': 'password'
}

valid_login = {'username': test_user['username'], 'password': test_user['password']}

def LoggedInClient(login=valid_login):
    """ Returns a logged-in client """
    client = TestApiClient()
    client.post(login_url, format='json', data=login)
    return client

def append_slash(string):
    """ Appends a forward slash to a string if it doesn't have one at the end """
    if (string[-1] != '/'):
        string += '/'
    return string
