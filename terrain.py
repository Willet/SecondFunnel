from lettuce import world, before
from selenium import webdriver
import lettuce_webdriver.webdriver

# Anything added to `world` is accessible in our step definitions
# Extremely useful for definining common steps, or environment setup
# More information here: http://lettuce.it/reference/terrain.html

# For more information on tests involving email, checkout this link:
# https://docs.djangoproject.com/en/dev/topics/testing/#email-services
# As recommended from this question on SO:
# http://stackoverflow.com/questions/7795529/using-lettuce-how-can-i-verify-that-an-email-sent-from-a-django-web-application

# This global `terrain.py` file will be executed before any other `terrain.py`

#@before.all
#def setup_browser():
#    # TODO: How can we run this with different browsers
#    world.browser = webdriver.Firefox()