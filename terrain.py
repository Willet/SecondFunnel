import re
import os
from time import sleep
from django.conf import settings
from lettuce import world, before, step, after
from lettuce.django import django_url
from lettuce_webdriver.webdriver import *
from nose.tools import ok_
from selenium import webdriver

# Fixes
# https://github.com/gabrielfalcao/lettuce/issues/215
world.mail_dir = os.path.join(os.getcwd(), "test")

@before.handle_request
def override_mail_settings(httpd, server):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    settings.EMAIL_FILE_PATH = world.mail_dir

# TODO: Cleanup mail folder on test completion
# TODO: Refactor terrain.py?

# Anything added to `world` is accessible in our step definitions
# Extremely useful for definining common steps, or environment setup
# More information here: http://lettuce.it/reference/terrain.html

# For more information on tests involving email, checkout this link:
# https://docs.djangoproject.com/en/dev/topics/testing/#email-services
# As recommended from this question on SO:
# http://stackoverflow.com/questions/7795529/using-lettuce-how-can-i-verify-that-an-email-sent-from-a-django-web-application

# This global `terrain.py` file will be executed before any other `terrain.py`

# Setup steps
@before.all
def setup_browser():
    # TODO: How can we run this with different browsers
    world.browser = webdriver.Firefox()

@after.each_scenario
def clear_session(scenario):
    world.browser.delete_all_cookies()

@after.all
def teardown_browser(total):
    world.browser.quit()

world.pages = {
    "login": django_url('/accounts/login/'),
    "store admin": django_url('/pinpoint/admin/'),
}

# Navigation steps
@world.absorb
@step(u'I visit the "([^"]*)" page')
def visit_page(step, page_name):
    page = world.pages.get(page_name)
    ok_(page != None, "Page does not exist in tests")
    visit(step, page)

@world.absorb
@step(u'I see the "([^"]*)" page')
def verify_page(step, page_name):
    page = world.pages.get(page_name)
    ok_(page != None, "Page does not exist in tests")
    url_should_contain(step, page)

# Mail steps
def get_mail(desc=False):
    filenames = os.listdir(world.mail_dir)

    # Sort by name, since names are approximately numeric
    filenames.sort()
    if desc:
        filenames.reverse()

    files = []
    for filename in filenames:
        file = parse_mail(filename)
        files.append(file)

    return files

def parse_mail(filename):
    path = os.path.join(world.mail_dir, filename)
    try:
        with open(path) as f:
            content = f.readlines()
    except:
        content = []

    headers    = {}
    body_index = 0

    for number, line in enumerate(content):
        h            = line.split(":")
        key          = h[0].lower().strip()
        value        = h[1].strip()
        headers[key] = value

        if key == "message-id":
            body_index = number + 1
            break

    body = "".join(content[body_index:]).strip()

    return {
        "headers": headers,
        "body"   : body
    }

@step(u'I receive an email titled "([^"]*)"')
def email_received(step, title):
    sleep(1)
    mail = get_mail(desc=True)
    ok_(len(mail) >= 1, "Haven't received any messages")
    ok_(mail[0]['headers'].get('subject') == title)

@step(u'visit the link in the email')
def visit_email_link(step):
    mail  = get_mail(desc=True)

    # Alternatively, could use something like beautiful soup to parse...
    regex  = re.compile(r'<a(?:.*)>(.*)</a>', re.MULTILINE)
    result = regex.search(mail[0]['body'])

    ok_(result is not None, "No links found in email")

    # Take the first result
    url = result.groups()[0]
    visit(step, url)

# TODO: Write function to distinguish whether to use 'press' or 'click'
# TODO: Add lettuce_selenium steps to world