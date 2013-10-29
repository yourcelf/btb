import time
from .base import BtbLiveServerTestCase

from django.contrib.auth.models import User
from scanblog.comments.models import Comment, Favorite

class TestComments(BtbLiveServerTestCase):
    def test_comment_while_not_signed_in(self):
        s = self.selenium
        s.get(self.url("/accounts/logout/"))
        s.get(self.url(self.doc.get_absolute_url()))
        self.assertEquals(Comment.objects.count(), 0)

        s.find_element_by_name("comment").send_keys("My Unique 12345 comment")
        s.find_element_by_xpath('//input[@type="submit"]').submit()

        self.wait(lambda s: s.current_url.startswith(self.url("/accounts/login")))
        s.find_element_by_name("username").send_keys("testuser")
        time.sleep(0.1) #ugh
        s.find_element_by_name("password").send_keys("testuser")
        s.find_element_by_xpath('//input[@type="submit"]').submit()
        self.wait(lambda s: not s.current_url.startswith(self.url("/accounts/login")))

        self.assert_current_url_is(self.doc.get_absolute_url() + "#c1")
        self.assertEquals(Comment.objects.count(), 1)
        self.assertTrue(
                "My Unique 12345 comment" in self.css(".commentbody").text
        )

    def test_add_comment_while_signed_in(self):
        s = self.selenium

        self.sign_in("testuser", "testuser")
        s.get(self.url(self.doc.get_absolute_url()))
        self.assertEquals(Comment.objects.count(), 0)

        s.find_element_by_name("comment").send_keys("My Unique 54321 comment")
        s.find_element_by_xpath('//input[@type="submit"]').submit()

        self.wait(lambda s: s.current_url.startswith(self.url(self.doc.get_absolute_url())))
        self.assertEquals(Comment.objects.count(), 1)
        self.assertTrue("My Unique 54321 comment" in self.css(".commentbody").text)

    def test_edit_my_comment(self):
        s = self.selenium
        self.sign_in("testuser", "testuser")
        comment = Comment.objects.create(user=User.objects.get(username="testuser"),
                comment="My Unique 31254 comment",
                document=self.doc)
        s.get(self.url(self.doc.get_absolute_url()))
        self.css(".comment-edit").click()
        s.find_element_by_id("id_comment").send_keys("My Unique 99999 comment")
        s.find_element_by_xpath('//input[@type="submit"]').submit()
        self.wait(lambda s: s.current_url.startswith(self.url(self.doc.get_absolute_url())))
        self.assertTrue("My Unique 99999 comment" in self.css(".commentbody").text)

    def test_delete_my_comment(self):
        s = self.selenium
        self.sign_in("testuser", "testuser")
        comment = Comment.objects.create(user=User.objects.get(username="testuser"),
                comment="My Unique 82753 comment",
                document=self.doc)
        s.get(self.url(self.doc.get_absolute_url()))
        for comment in self.csss(".commentbody"):
            if "My Unique 82753 comment" in comment.text:
                break
        else:
            self.assertFail("Comment not found.")
        self.css(".comment-delete").click()
        self.css(".delete-form")
        s.find_element_by_xpath('//input[@type="submit"]').submit()
        self.wait(lambda s: s.current_url.startswith(self.url(self.doc.get_absolute_url())))
        self.assertFalse("My Unique 82753 comment" in self.css(".comments").text)
        for comment in self.csss(".commentbody"):
            if "My Unique 82753 comment" in comment.text:
                self.assertFail("Comment shouldn't've been found.")

    def test_add_favorite(self):
        s = self.selenium
        self.sign_in("testuser", "testuser")
        s.get(self.url(self.doc.get_absolute_url()))

        self.css(".favorite-button").click()

        self.assertEquals(Favorite.objects.count(), 1)
        fav = Favorite.objects.all()[0]
        self.assertTrue(fav.document == self.doc)
        self.assertEquals(len(self.csss(".favorite-button.active")), 1)
        self.assertEquals(len(self.csss(".get-favorites")), 1)

        self.css(".get-favorites").click()
        self.wait(lambda b: len(self.csss(".favorites-popover .content li")) == 1)
        self.css(".favorites-popover .content li a").click()
        self.assertTrue("testuser's profile" in s.title)
        self.assertEquals(len(self.csss("li.favorite")), 1)
        self.css("li.favorite .favorites-control .favorite-button").click()
        self.assertEquals(Favorite.objects.count(), 0)

        s.get(self.url("/people/show"))
        self.assertEquals(len(self.csss("li.favorite")), 0)

    def test_add_favorite_before_login(self):
        s = self.selenium
        s.get(self.url("/accounts/logout/"))
        s.get(self.url(self.doc.get_absolute_url()))
        self.css(".favorite-button").click()

        self.wait(lambda b: "Login" in s.title)
        self.css("#id_username").send_keys("testuser")
        self.css("#id_password").send_keys("testuser")
        self.click_button("Login")

        self.assertTrue(self.doc.get_title() in s.title)
        self.assertEquals(len(self.csss(".favorite-button.active")), 1)
        self.assertTrue("Favorite" in self.css("li.message").text)
