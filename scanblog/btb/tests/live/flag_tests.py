from .base import BtbLiveServerTestCase

from comments.models import Comment
from django.contrib.auth.models import User

class TestFlags(BtbLiveServerTestCase):
    def test_flag_a_post(self):
        s = self.selenium
        s.get(self.url("/accounts/logout/"))
        s.get(self.url(self.doc.get_absolute_url()))
        self.css(".flag-top-button").click()

        self.wait(lambda s: s.current_url.startswith(self.url("/accounts/login/")))
        s.find_element_by_name("username").send_keys("testuser")
        s.find_element_by_name("password").send_keys("testuser")
        s.find_element_by_xpath('//input[@type="submit"]').submit()
        self.wait(lambda s: not s.current_url.startswith(self.url("/accounts/login/")))

        s.find_element_by_id("id_reason").send_keys("This is problematic")
        s.find_element_by_xpath('//input[@type="submit"]').submit()
        self.wait(lambda s: s.current_url.startswith(self.url(self.doc.get_absolute_url())))
        for msg in self.csss(".message"):
            if "moderator will review that" in msg.text:
                return
        else:
            assert 0, "Confirmation not found"
        Note.objects.get(creator=User.objects.get(username="testuser"), 
                text__contains="FLAG from user")

    def test_flag_a_comment(self):
        s = self.selenium
        Comment.objects.create(
                user=User.objects.create(username="testuser1"),
                comment="My comment",
                document=self.doc)
        self.sign_in("testuser", "testuser")
        s.get(self.url(self.doc.get_absolute_url()))
        self.css(".comment-flag").click()
        s.find_element_by_id("id_reason").send_keys("This comment has problems")
        s.find_element_by_xpath('//input[@type="submit"]').submit()
        self.wait(lambda s: s.current_url.startswith(self.url(self.doc.get_absolute_url())))

        for msg in self.csss(".message"):
            if "moderator will review that" in msg.text:
                return
        else:
            assert 0, "Confirmation not found"
        Note.objects.get(creator=User.objects.get(username="testuser"), 
                text__contains="FLAG from user")
