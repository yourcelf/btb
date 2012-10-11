import os
import time
import shutil

from .base import BtbLiveServerTestCase, NoSuchElementException
from django.conf import settings
from django.test.utils import override_settings

from scanning.models import Scan
from django.contrib.auth.models import User

class TestModUploads(BtbLiveServerTestCase):
    def setUp(self):
        super(TestModUploads, self).setUp()
        self.applied_tasks = []
    def tearDown(self):
        super(TestModUploads, self).tearDown()
        for s in Scan.objects.all():
            s.full_delete()

    def upload_file(self, path, number_of_scans):
        assert os.path.exists(path)
        assert Scan.objects.count() == 0
        b = self.selenium
        b.get(self.url("/"))
        b.find_element_by_link_text("Upload").click()
        self.assertEquals(self.css("h1").text, "Upload Scans")
        el = self.css("#id_file")
        el.send_keys(path)
        self.css(".upload-submit").submit()
        self.wait(lambda b: not b.current_url.startswith(self.url("/scanning/add")))

        while b.current_url.startswith(self.url("/moderation/wait")):
            try:
                el = self.css(".error")
                assert False, el.text
            except NoSuchElementException:
                time.sleep(1)

        if number_of_scans == 1:
            self.wait(lambda b: self.css("h1").text == "Split Scan")
            self.assertTrue(b.current_url.startswith(self.url("/moderation/#/process")))
        else:
            time.sleep(5)
            self.assertEquals(b.current_url, self.url("/moderation/"))
            self.wait(lambda b: len(self.csss(".open-scans .scan")) == number_of_scans, 60)

        for s in Scan.objects.all():
            s.full_delete()

    def test_upload(self):
        self.sign_in("testmod", "testmod")
        for filename, count in [
                ("unixzip.zip", 2),
                ("maczip.zip", 2),
                ("ex-req-post-photo.pdf", 1)]:
            self.upload_file(
                os.path.join(settings.MEDIA_ROOT, "test", "src", filename),
                count
            )
