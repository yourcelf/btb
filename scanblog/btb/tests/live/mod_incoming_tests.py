# -*- coding: utf-8 -*-

import time
from .base import BtbLiveServerTestCase

from scanning.models import PendingScan

class TestModIncoming(BtbLiveServerTestCase):
    def test_add_and_manage_pending_scans(self):
        b = self.selenium
        assert PendingScan.objects.count() == 0

        self.sign_in("testmod", "testmod")
        b.find_element_by_link_text("Moderation").click()
        b.find_element_by_link_text("Incoming mail").click()
        self.wait(lambda b: len(self.csss(".pending-scans")) > 0)

        # Add a pending scan for Test Author.
        self.css(".user-chooser-trigger").send_keys("t")
        self.wait(lambda b: len(self.csss(".user-search")) > 0)
        self.css(".user-search").send_keys("est author")
        self.csss(".user-chooser .results .result")[0].click()
        self.wait(lambda b: len(self.csss(".pending-scan-list .user-compact")) > 0)
        self.assertTrue("Test Author" in self.csss(".pending-scan-list .user-compact")[0].text)

        # Mark the pending scan missing.
        self.csss("input.pending-scan-missing")[0].click()
        self.wait(lambda b: PendingScan.objects.missing().count() == 1)

        # Reload, and see that the pending scan list is empty.
        time.sleep(0.5) # Wait for any AJAX requests to finish before navigating.
        b.get(self.url("/moderation/"))
        b.find_element_by_link_text("Moderation").click()
        b.find_element_by_link_text("Incoming mail").click()
        # wait for load
        self.wait(lambda b: self.css("h1").text == "Incoming Mail")
        self.assertEquals(len(self.csss(".pending-scan-list .user-compact")), 0)

        # Check the missing scan list.
        self.css(".show-missing").click()
        self.wait(lambda b: len(self.csss(".pending-scan-list .user-compact")) > 0)
        self.assertTrue("Test Author" in self.csss(".pending-scan-list .user-compact")[0].text)

        # Delete the choice.
        self.css(".remove-pending-scan").click()
        self.wait(lambda b: len(self.csss(".pending-scan-list .user-compact")) == 0)
        self.assertEquals(PendingScan.objects.count(), 0)
