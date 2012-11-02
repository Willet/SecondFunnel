from lettuce import step, world
from lettuce_webdriver.webdriver import *

@step(u'I login with username "(.*?)" and password "(.*?)"$')
def successful_login(step, user, password):
    world.visit_page(step, "login")
    fill_in_textfield(step, "username", user)
    fill_in_textfield(step, "password", password)
    press_button(step, "login")