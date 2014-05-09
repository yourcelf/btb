# -*- coding: utf-8 -*-
from .base import BtbLiveServerTestCase

from django.contrib.auth.models import User

class TestModUsers(BtbLiveServerTestCase):
    def search_for_user(self, name):
        b = self.selenium
        b.get(self.url("/moderation/"))
        b.find_element_by_link_text("Manage users").click()
        self.wait(lambda b: len(self.csss(".user-chooser-trigger")) > 0)

        self.css(".user-chooser-trigger").send_keys(name[0])
        self.wait(lambda b: len(self.csss(".user-search")) > 0)
        self.css(".user-search").send_keys(name[1:])

    def search_for_nonexistent_account_and_create_one(self, username):
        b = self.selenium
        self.sign_in("testmod", "testmod")
        assert not User.objects.filter(profile__display_name=username).exists()
        self.search_for_user(username)

        self.assertEquals(
            self.css(".user-chooser-holder .results .noresult").text,
            "No results."
        )

        self.css(".user-chooser-holder .add-user-link").click()
        assert self.css(".user-chooser-holder form.add-user")
        self.assertEquals(
            self.css(".user-chooser-holder input[name=display_name]").get_attribute("value"),
            username
        )
        self.css(".user-chooser-holder textarea[name=mailing_address]").send_keys(
                "77 Amherst St\nCambridge, MA")
        self.css("input[type=submit]").click()

        self.wait(lambda b: User.objects.filter(profile__display_name=username).exists())
        # Wait for all ajax calls from user detail page to finish.
        self.wait(lambda b: all(
                "No results" in self.css(s).text for s in [
                    ".profilelist", ".postlist", ".requestlist", ".photolist",
                    ".missingscanlist", ".licenselist"
                ]
        ))

        self.search_for_user(username.lower())
        for el in self.csss(".user-chooser-holder .results .display-name"):
            if el.text == username:
                break
        else:
            self.assertFail("User not found in user search.")

        User.objects.get(profile__display_name=username).delete()

    def test_search_for_nonexistent_user(self):
        self.search_for_nonexistent_account_and_create_one("George Doesnotexist")
        self.search_for_nonexistent_account_and_create_one("Doesnotexist With A Very Long Name")
