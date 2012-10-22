from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from unittest import skip
import time

class AdminTest(LiveServerTestCase):
    fixtures = ['test_data.json']

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)

    def tearDown(self):
        self.browser.quit()

    def test_can_log_into_admin_site(self):
        # Gertrude opens her web browser, and goes to the admin page
        self.browser.get(self.live_server_url + '/admin/')

        # She sees the familiar 'Django administration' heading
        body = self.browser.find_element_by_tag_name('body')
        self.assertIn('Django administration', body.text)

        username_field = self.browser.find_element_by_id('id_username')
        username_field.send_keys("terrance")

        username_field = self.browser.find_element_by_id('id_password')
        username_field.send_keys("asdf")
        username_field.send_keys(Keys.RETURN)

        body = self.browser.find_element_by_tag_name('body')
        self.assertIn('Site administration', body.text)


class PasswordChangeTest(LiveServerTestCase):
    fixtures = ['test_data.json']

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://localhost:8000"
        self.verificationErrors = []
    
    def test_password_change(self):
        driver = self.driver

        # go to django admin page and log in since we can't on ours yet
        driver.get(self.base_url + "/admin/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("terrance")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("asdf")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()

        # go to second funnel login page and click change password
        driver.get(self.base_url + "/accounts/login/")
        driver.find_element_by_link_text("Change Password").click()

        # fill in change password form
        driver.find_element_by_id("id_old_password").clear()
        driver.find_element_by_id("id_old_password").send_keys("asdf")
        driver.find_element_by_id("id_new_password1").clear()
        driver.find_element_by_id("id_new_password1").send_keys("qwert")
        driver.find_element_by_id("id_new_password2").clear()
        driver.find_element_by_id("id_new_password2").send_keys("qwert")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()

        # log out
        driver.find_element_by_link_text("Logout").click()

        # try logging back in with new password
        driver.get(self.base_url + "/admin/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("terrance")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("qwert")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()

        # make sure django admin page loaded
        body = driver.find_element_by_tag_name('body')
        self.assertIn('Site administration', body.text)
    
    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

@skip("currently broken: email does not send")
class PasswordResetTest(LiveServerTestCase):
    fixtures = ['test_data.json']

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(3)
        self.base_url = "/"
        self.verificationErrors = []
    
    def test_can_recover_password(self):
        driver = self.driver
        driver.get(self.live_server_url + "/accounts/login/")
        driver.find_element_by_css_selector(".grid_12 > p > a").click()
        driver.find_element_by_id("id_email").clear()
        driver.find_element_by_id("id_email").send_keys("TNiechciol@gmail.com")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        time.sleep(5)
        driver.get("http://localhost:1080/")
        driver.find_element_by_xpath("//tr[last()]/td").click()
        # http://stackoverflow.com/questions/7575827/selenium-and-iframe
        # ERROR: Caught exception [unknown command []]
        #driver.switchTo().frame("foo");
        driver.switch_to_frame(driver.find_element_by_css_selector("#message iframe.body"))
        driver.find_element_by_css_selector("a").click()
        driver.find_element_by_id("id_new_password1").clear()
        driver.find_element_by_id("id_new_password1").send_keys("qwerty")
        driver.find_element_by_id("id_new_password2").clear()
        driver.find_element_by_id("id_new_password2").send_keys("qwerty")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        driver.find_element_by_link_text("Log in.").click()
    
    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

