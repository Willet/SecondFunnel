from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from unittest import skip
import time

def login(cls):
    """
    Logging is a common action so just put it outside of test classes
    """
    driver = cls.driver

    # go to login page and log in
    driver.get("%s%s" % (cls.live_server_url, "/accounts/login/"))

    driver.find_element_by_id("id_username").clear()
    driver.find_element_by_id("id_username").send_keys("terrance")
    driver.find_element_by_id("id_password").clear()
    driver.find_element_by_id("id_password").send_keys("asdf")
    driver.find_element_by_css_selector("input[type=\"submit\"]").click()


class AccountTests(LiveServerTestCase):
    """
    Tests basic account-related functionality
    login/logout/password/etc
    """

    fixtures = ['test_data.json']
    driver = None
    verificationErrors = None

    @classmethod
    def setUpClass(cls):
        AccountTests.driver = webdriver.Firefox()
        AccountTests.driver.implicitly_wait(30)
        AccountTests.verificationErrors = []
        super(AccountTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        AccountTests.driver.quit()
        super(AccountTests, cls).tearDownClass()

    def test_login_logout(self):
        driver = self.driver

        # go to login page and log in
        login(self)

        # make sure pinpoint admin page loaded
        body = driver.find_element_by_tag_name('body')
        self.assertIn('PinPoint Admin', body.text)

        # log out
        driver.find_element_by_link_text("Logout").click()

        # make sure log in page loaded and it doesn't already say we're logged in
        body = driver.find_element_by_tag_name('body')
        self.assertIn('Username', body.text)

    def test_password_change(self):
        driver = self.driver

        # go to login page and log in
        login(self)

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
        login(self)

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


class FeaturedProductWizardTests(LiveServerTestCase):
    """
    Test featured product wizard related functionality
    creating and editing campaigns
    """

    fixtures = ['test_data.json']
    driver = None
    verificationErrors = None

    @classmethod
    def setUpClass(cls):
        FeaturedProductWizardTests.driver = webdriver.Firefox()
        FeaturedProductWizardTests.driver.implicitly_wait(30)
        FeaturedProductWizardTests.verificationErrors = []
        super(FeaturedProductWizardTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        FeaturedProductWizardTests.driver.quit()
        super(FeaturedProductWizardTests, cls).tearDownClass()


    def test_make_new_campaign(self):
        driver = self.driver

        login(self)

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
        driver = self.driver

        login(self)

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
