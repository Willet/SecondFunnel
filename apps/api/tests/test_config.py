base_url = '/graph/v1'
login_url = base_url + '/user/login/'
logout_url = base_url + '/user/logout/'
restricted_url = base_url + '/store'
proxy_url = base_url

# TODO fix (could not dump data)
# the following fixture should include test data that we add to the DB for testing
# fixtures = ['api_tests.json']

# We will assume gap/gap is a valid user for now as I don't have fixtures yet
# TODO Replace when we have a fixture with test data
valid_login = {'username': 'gap', 'email': 'gap@gap.secondfunnel.com',
               'password': 'gap'}
