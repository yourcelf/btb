# -*- coding: utf-8 -*-
import os
import shutil
from django.conf import settings
from .base import BtbLiveServerTestCase

from django.contrib.auth.models import User
from scanning.models import Scan, Document
from comments.models import Comment

class TestTranscriptions(BtbLiveServerTestCase):
    def setUp(self):
        super(TestTranscriptions, self).setUp()

        pdf = shutil.copy(
            os.path.join(settings.MEDIA_ROOT, "test", "src", "ex-post-prof-license.pdf"),
            os.path.join(settings.MEDIA_ROOT, "test", "test_post.pdf")
        )

        self.scan = Scan.objects.create(
                author=User.objects.get(username="testauthor"),
                uploader=User.objects.get(username="testmod"),
                pdf=os.path.join("test", "test_post.pdf"),
                processing_complete=True,
        )
        self.scan_doc = Document.objects.create(
            title="Scaney",
            status="published",
            type="post",
            author=User.objects.get(username="testauthor"),
            editor=User.objects.get(username="testmod"),
            scan=self.scan,
            pdf=os.path.join("test", "test_post.pdf"),
        )

    def tearDown(self):
        super(TestTranscriptions, self).tearDown()
        self.scan.delete()
        try:
            os.remove(os.path.join(settings.MEDIA_ROOT, "test", "test_post.pdf"))
        except OSError:
            pass

    def test_transcribe_while_logged_out(self):
        b = self.selenium
        b.get(self.url("/accounts/logout/"))
        b.get(self.url("/scanning/transcribe/%s" % self.scan_doc.pk))
        # redirects to login.
        self.wait(lambda b: b.current_url.startswith(self.url("/accounts/login")))

    def test_start_transcription(self):
        b = self.selenium
        self.sign_in("testuser", "testuser")

        # I've previously left no comments; so I'll get a post-transcription prompt.
        assert len(Comment.objects.filter(document=self.scan_doc)) == 0

        # Do the transcription.
        b.get(self.url(self.scan_doc.get_absolute_url()))
        self.css(".transcribe-top-button").click()
        self.css("#id_body").send_keys("This is a transcription")
        b.find_element_by_xpath('//input[@type="submit"]').submit()

        # Post transcription comment
        self.wait(lambda b: not b.current_url.startswith("/scanning/transcribe"))
        self.assertTrue("Thanks for writing!" in self.css("#id_comment").text)
        b.find_element_by_xpath('//input[@type="submit"]').submit()
        self.wait(lambda b: b.current_url.startswith(self.url(self.scan_doc.get_absolute_url())))

        # Verify.
        self.assertEquals(
            self.css(".transcription").text.strip(),
            "This is a transcription"
        )
        self.assertEquals(
            self.css(".transcribe-top-button").text,
            u"✍ Partially transcribed"
        )

    def test_complete_transcription(self):
        b = self.selenium
        self.sign_in("testuser", "testuser")
        Comment.objects.create(
                comment="The comment",
                document=self.scan_doc,
                user=User.objects.get(username="testuser"),
        )
        assert len(Comment.objects.filter(
            document=self.scan_doc, user__username="testuser")) > 0


        # Do the transcription.
        b.get(self.url(self.scan_doc.get_absolute_url()))
        self.css(".transcribe-top-button").click()
        self.css("#id_body").send_keys("This is a complete transcription")
        self.set_checkbox(b.find_element_by_name("complete"), True)
        b.find_element_by_xpath('//input[@type="submit"]').submit()

        # Since there's a previous comment, skip the post-transcription comment.
        self.wait(lambda b: b.current_url.startswith(self.url(self.scan_doc.get_absolute_url())))

        # Verify.
        self.assertEquals(
            self.css(".transcription").text.strip(),
            "This is a complete transcription"
        )
        self.assertEquals(
            self.css(".transcribe-top-button").text,
            u"✍ Transcribed"
        )






