from django.test import LiveServerTestCase

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

from django.contrib.auth.models import User, Group
from profiles.models import Organization
from scanning.models import Document

class BtbLiveServerTestCase(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(4)
        super(BtbLiveServerTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()

    def create_user(self, username, password=None, email="",
            user_kwargs=None, profile_kwargs=None, groups=None):
        u, created = User.objects.get_or_create(username=username)
        u.email = email
        u.set_password(password or username)
        for prop, val in (user_kwargs or {}).items():
            setattr(u, prop, val)
        u.save()
        for prop, val in (profile_kwargs or {}).items():
            setattr(u.profile, prop, val)
        u.profile.save()

        for group in groups or []:
            u.groups.add(Group.objects.get(name=group))
        return u

    def add_test_users(self):
        # Commenter
        self.create_user("testuser")

        # Organization
        o, created = Organization.objects.get_or_create(
                name="testorg", slug="testorg")

        # Moderator
        u = self.create_user("testmod", groups=["moderators"])
        o.moderators.add(u)

        # Author
        u = self.create_user("testauthor", profile_kwargs=dict(
            display_name="Test Author",
            blogger=True,
            managed=True,
            consent_form_received=True))
        o.members.add(u)

        # Unmanaged author
        u = self.create_user("testunmanaged", profile_kwargs=dict(
            display_name="Test Unmanaged",
            blogger=True,
            managed=False,
            consent_form_received=True,
        ))
        o.members.add(u)

    def setUp(self):
        self.add_test_users()

    def url(self, arg):
        return "".join((self.live_server_url, arg))

    def css(self, selector):
        return self.selenium.find_element_by_css_selector(selector)

    def csss(self, selector):
        return self.selenium.find_elements_by_css_selector(selector)

    def hard_click(self, el):
        chain = ActionChains(self.selenium)
        chain.move_to_element(el)
        chain.click_and_hold(el)
        chain.release(None)
        chain.perform()

    def click_button(self, text):
        el = self.selenium.find_element_by_xpath('//input[@value="%s"]' % text)
        el.click()

    def assert_current_url_is(self, url):
        self.assertEquals(self.selenium.current_url, self.url(url))

    def assert_redirected_to_login(self):
        self.wait(lambda s: s.current_url.startswith(self.url("/accounts/login")))

    def sign_in(self, username, password):
        s = self.selenium
        # I am not signed in.
        s.get(self.url("/accounts/logout/?next=/"))
        # I access the url "/"
        s.get(self.url("/"))
        # I click "Sign in"
        s.find_element_by_link_text("Sign in").click()
        # I see the login form
        self.assertTrue(bool(self.css(".login-form")))
        # I see the registration form"
        self.assertTrue(bool(self.css(".register-form")))
        # I login as "testuser:testuser"
        uname_el = self.selenium.find_element_by_id("id_username")
        uname_el.send_keys(username)
        pword_el = self.selenium.find_element_by_id("id_password")
        pword_el.send_keys(password)
        self.click_button("Login")
        self.wait(lambda s: not s.current_url.startswith(self.url("/accounts/login")))
        self.assert_current_url_is("/")
        self.assertTrue(username in self.css(".auth").text)

    def wait(self, func, timeout=4):
        WebDriverWait(self.selenium, timeout).until(func)

    def create_test_doc(self, **kwargs):
        base = dict(
            body="This is my lovely post.",
            type="post",
            title="Lovely",
            status="published",
            adult=False,
            editor=User.objects.get(username="testmod"),
            author=User.objects.get(username="testunmanaged"),
        )
        base.update(kwargs)
        return Document.objects.get_or_create(**base)[0]

