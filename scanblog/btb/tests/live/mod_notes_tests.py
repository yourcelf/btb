import time

from .base import BtbLiveServerTestCase
from annotations.models import Note

class TestModNotes(BtbLiveServerTestCase):
    def test_create_ticket(self):
        b = self.selenium
        self.sign_in("testmod", "testmod")
        b.get(self.url(self.doc.get_edit_url()))
        self.css(".add-note").click()
        self.css(".note-editor textarea[name=text]").send_keys("Here is a note")

        b.execute_script("$('input.save-note')[0].scrollIntoView()")
        self.css("input.save-note").click()

        self.wait(lambda b: len(self.csss(".note-table .note .body")) > 0)
        self.assertEquals(Note.objects.count(), 1)
        self.assertEquals(Note.objects.open_tickets().count(), 0)
        self.assertEquals(Note.objects.closed_tickets().count(), 1)

        self.assertTrue("Here is a note" in self.css(".note-table .note .body").text)
        self.css(".note-table .note .byline .edit-note").click()
        self.wait(lambda b: len(self.csss(".save-note")) > 0)

        self.css(".note-editor textarea[name=text]").send_keys(". Moar note.")
        self.css("input[name=important]").click()
        self.css("input[name=needsResolution]").click()
        b.execute_script("$('input.save-note')[0].scrollIntoView()")
        self.css("input.save-note").click()
        self.wait(lambda b: "Moar note" in self.css(".note-table .note .body").text)
        self.assertTrue("NEEDS ATTENTION" in self.css(".note .body.important .status").text)
        self.assertEquals(Note.objects.count(), 1)
        self.assertEquals(Note.objects.open_tickets().count(), 1)
        self.assertEquals(Note.objects.closed_tickets().count(), 0)

        # And it appears in dashboard now..
        b.get(self.url("/moderation/"))
        self.wait(lambda b: len(self.csss(".note-table .note .body")) > 0)
        self.assertTrue("Here is a note. Moar note." in self.css(".note-table .note .body").text)

        # And we can mark it resolved.
        self.css(".mark-resolved").click()
        self.wait(lambda b: len(self.csss(".mark-resolved")) == 0)
        self.assertEquals(Note.objects.count(), 1)
        self.assertEquals(Note.objects.open_tickets().count(), 0)
        self.assertEquals(Note.objects.closed_tickets().count(), 1)
