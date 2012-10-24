from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from unittest import skip
import time

class Tests(LiveServerTestCase):
    fixtures = ['test_data.json']
    driver = None
    verificationErrors = None

    @classmethod
    def setUpClass(cls):
        Tests.driver = webdriver.Firefox()
        Tests.driver.implicitly_wait(30)
        Tests.verificationErrors = []
        super(Tests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        Tests.driver.quit()
        super(Tests, cls).tearDownClass()

    def test_can_log_into_admin_site(self):
        driver = Tests.driver

        # Gertrude opens her web browser, and goes to the admin page
        self.driver.get(self.live_server_url + '/admin/')

        # She sees the familiar 'Django administration' heading
        body = self.driver.find_element_by_tag_name('body')
        self.assertIn('Django administration', body.text)

        username_field = self.driver.find_element_by_id('id_username')
        username_field.send_keys("terrance")

        username_field = self.driver.find_element_by_id('id_password')
        username_field.send_keys("asdf")
        username_field.send_keys(Keys.RETURN)

        body = self.driver.find_element_by_tag_name('body')
        self.assertIn('Site administration', body.text)

    def test_login_logout(self):
        driver = Tests.driver

        # go to login page and log in
        driver.get(self.live_server_url + "/accounts/login/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("terrance")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("asdf")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()

        # make sure pinpoint admin page loaded
        body = driver.find_element_by_tag_name('body')
        self.assertIn('PinPoint Admin', body.text)

        # log out
        driver.find_element_by_link_text("Logout").click()

        # make sure log in page loaded and it doesn't already say we're logged in
        body = driver.find_element_by_tag_name('body')
        self.assertIn('Username', body.text)

    def test_login_logout(self):
        driver = Tests.driver

        # go to login page and log in
        driver.get(self.live_server_url + "/accounts/login/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("terrance")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("asdf")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()

        # make sure pinpoint admin page loaded
        body = driver.find_element_by_tag_name('body')
        self.assertIn('PinPoint Admin', body.text)

        # log out
        driver.find_element_by_link_text("Logout").click()

        # make sure log in page loaded and it doesn't already say we're logged in
        body = driver.find_element_by_tag_name('body')
        self.assertIn('Username', body.text)

    def test_make_new_campaign(self):
        driver = Tests.driver

        # go to login page and log in
        driver.get(self.live_server_url + "/accounts/login/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("terrance")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("asdf")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()

        driver.find_element_by_link_text("New Page").click()

        driver.find_element_by_css_selector(".block_type:nth-of-type(1) a").click()

        driver.find_element_by_id("id_name").clear()
        driver.find_element_by_id("id_name").send_keys("newcampaign")

        driver.find_element_by_id("product_name").clear()
        driver.find_element_by_id("product_name").send_keys("HTML5 FOR WEB DESIGNERS")

        time.sleep(1)

        driver.find_element_by_xpath('//html/body/ul/li/a[. = "HTML5 FOR WEB DESIGNERS"]').click()

        time.sleep(1)

        driver.find_element_by_css_selector("#product_images > li:nth-of-type(1) img").click()

        driver.find_element_by_css_selector(".actions .button").click()

        driver.find_element_by_css_selector(".actions .button[data-action=publish]").click()

        body = driver.find_element_by_tag_name('body')
        self.assertIn('PinPoint Admin: A Book Apart', body.text)
        self.assertIn('newcampaign', body.text)

        # log out
        driver.find_element_by_link_text("Logout").click()

        # make sure log in page loaded and it doesn't already say we're logged in
        body = driver.find_element_by_tag_name('body')
        self.assertIn('Username', body.text)

    def test_no_image_selected_error(self):
        driver = Tests.driver

        # go to login page and log in
        driver.get(self.live_server_url + "/accounts/login/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("terrance")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("asdf")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()

        driver.find_element_by_link_text("New Page").click()

        driver.find_element_by_css_selector(".block_type:nth-of-type(1) a").click()

        driver.find_element_by_id("id_name").clear()
        driver.find_element_by_id("id_name").send_keys("newcampaign")

        driver.find_element_by_id("product_name").clear()
        driver.find_element_by_id("product_name").send_keys("HTML5 FOR WEB DESIGNERS")

        time.sleep(1)

        driver.find_element_by_xpath('//html/body/ul/li/a[. = "HTML5 FOR WEB DESIGNERS"]').click()

        time.sleep(1)

        driver.find_element_by_css_selector(".actions .button").click()

        body = driver.find_element_by_tag_name('body')
        self.assertIn('Please either select an existing product image or upload a custom one.', body.text)

    def test_password_change(self):
        driver = Tests.driver

        # go to login page and log in
        driver.get(self.live_server_url + "/accounts/login/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("terrance")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("asdf")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()

        # we should have been redirected to the admin page
        # click on the profile page link
        driver.find_element_by_link_text("Profile Page").click()

        # click on the change password link
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
        driver.get(self.live_server_url + "/accounts/login/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("terrance")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("qwert")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()

    @skip("currently broken: email does not send")
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
