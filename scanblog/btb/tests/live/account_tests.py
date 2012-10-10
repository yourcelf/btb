from .base import BtbLiveServerTestCase, NoSuchElementException

from django.contrib.auth.models import User, Group
from profiles.models import Organization
from scanning.models import Document
from comments.models import Comment

class TestAccounts(BtbLiveServerTestCase):
    def test_sign_in(self):
        self.sign_in("testuser", "testuser")

    def attempt_registration(self, username, email, password1, password2):
        s = self.selenium
        register_url = "/accounts/register/"
        welcome_url = "/accounts/welcome/"
        s.get(self.url(register_url))
        for el_name, val in zip(
                ("username", "email", "password1", "password2"),
                (username, email, password1, password2)):
            el = s.find_element_by_name(el_name)
            el.clear()
            el.send_keys(val)
        el.submit()

        try:
            self.css(".errorlist")
            self.assert_current_url_is(register_url)
            return False
        except NoSuchElementException:
            self.assert_current_url_is(welcome_url)
            self.assertTrue(username in self.css(".auth").text)
            return True

    def test_register(self):
        working_scenarios = [
            ("testuser1", "t@a.com", "testuser1", "testuser1"), # With email
            ("testuser1", "", "testuser1", "testuser1"), # Without
        ]
        failing_scenarios = [
            ("uploader", "", "pass", "pass"), # Account already exists
            ("testuser1", "", "doesnt", "matc"), # Passwords don't match
        ]
        for args in working_scenarios:
            self.assertTrue(self.attempt_registration(*args))
            User.objects.get(username=args[0]).delete()

        for args in failing_scenarios:
            self.assertFalse(self.attempt_registration(*args))

    def leave_a_comment(self, username, password):
        self.sign_in(username, password)
        self.create_test_doc()
        # There's no comment.
        self.assertEquals(Comment.objects.filter(
            user__username=username, comment="My comment").count(), 0)
        # Leave one.
        self.selenium.get(self.url(self.doc.get_absolute_url()))
        comment_entry = self.selenium.find_element_by_name("comment")
        comment_entry.send_keys("My comment")
        comment_entry.submit()
        self.assert_current_url_is(self.doc.get_absolute_url())
        # There is now a comment.
        self.wait(lambda s: Comment.objects.filter(
                user__username=username, comment="My comment").count() == 1)

    def delete_account(self, comments_too):
        s = self.selenium
        # ARGH -- selenium not functioning properly with hover...
        #self.hard_click(self.css(".auth .menu-trigger"))
        #self.hard_click(s.find_element_by_link_text("Profile"))
        s.get(self.url("/people/show"))
        s.find_element_by_link_text("Edit settings").click()
        s.find_element_by_link_text("Delete account").click()
        if comments_too:
            s.find_element_by_name("delete_comments").click()
        s.find_element_by_xpath('//input[@type="submit"]').submit()
        self.assertTrue("successfully deleted" in self.css(".message").text)

    def test_delete_account_leaving_comments(self):
        self.leave_a_comment("testuser", "testuser")
        pk = User.objects.get(username="testuser").pk
        self.assertEquals(Comment.objects.filter(user__pk=pk).count(), 1)
        self.delete_account(False)
        self.wait(lambda s: Comment.objects.filter(
                user__pk=pk, comment="My comment").count() == 1)

    def test_delete_account_removing_comments(self):
        self.leave_a_comment("testuser", "testuser")
        pk = User.objects.get(username="testuser").pk
        self.assertEquals(Comment.objects.filter(user__pk=pk).count(), 1)
        self.delete_account(True)
        self.wait(lambda s: Comment.objects.filter(
                user__pk=pk, comment="My comment").count() == 0)
