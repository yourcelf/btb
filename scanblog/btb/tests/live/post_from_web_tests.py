# -*- coding: utf-8 -*-
from .base import BtbLiveServerTestCase

class TestPostFromWeb(BtbLiveServerTestCase):
    def _add_post(self, status):
        self.selenium.get(self.url("/blogs/"))
        self.selenium.find_element_by_link_text("✍ Compose").click()
        self.css("#id_title").send_keys("My Title %s" % status)
        self.css("#id_body").send_keys("This is the body of my %s post" % status)
        # Tagging feature removed...
        #self.css(".tagit-input").send_keys("tag1, tag2, tag3")
        self.css("#id_status").send_keys(status)
        self.css("input[type=submit]").click()

    def test_post_from_web(self):
        b = self.selenium
        self.sign_in("testunmanaged", "testunmanaged")
        self._add_post("publish")

        b.get(self.url("/blogs/"))
        # Get the first link; we should be first since we just published.
        self.csss("a.read-more")[0].click()
        self.assertEquals(
                self.css("h2").text.strip(),
                "My Title publish"
        )

        self._add_post("draft")
        b.get(self.url("/blogs/"))
        for el in self.csss("h2"):
            if el.text.strip() == "My Title draft":
                self.assertFail("Draft was published.")

        b.get(self.url("/blogs/"))
        b.find_element_by_link_text("☰ My Blog Posts").click()
        for el in self.csss("a"):
            if el.text.strip() == "My Title draft":
                break
        else:
            self.assertFail("Draft not found in post manager.")

        # Should be 4 rows: header, two we just posted, and the one added by base class.
        self.assertEquals(len(self.csss(".my-posts tr")), 2 + 1 + 1)

        b.find_element_by_link_text("My Title draft").click()
        self.assertEquals(
                self.css("#id_title").get_attribute("value").strip(),
                "My Title draft"
        )
        self.assertEquals(
                self.css("#id_body").text.strip(),
                "This is the body of my draft post"
        )
