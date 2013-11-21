import re
import os
import json
import shutil
import datetime
from django.test import TestCase, LiveServerTestCase
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.files import File
from pyPdf import PdfFileReader

from btb.tests import BtbLoginTestCase
from correspondence import utils
from correspondence.models import StockResponse, Letter
from correspondence.views import needed_letters
from scanning.models import Scan, Document, DocumentPage
from scanning.tasks import split_scan, update_document_images
from comments.models import Comment, CommentRemoval, RemovalReason
from profiles.models import Profile, Organization

class TextLatexCompilation(TestCase):
    def test_escape_tex(self):
        self.assertEquals(
            utils.tex_escape('Line one\nLine two\nLine three'),
            'Line one\\\\\nLine two\\\\\nLine three'
        )
        self.assertEquals(
            utils.tex_escape('Line one\n\nLine three'),
            'Line one\\\\\n~\\\\\nLine three'
        )

class TestStockResponses(BtbLoginTestCase):
    def test_get_stock_response(self):
        stock_responses = [
                ["Stock 1", "The answer to your question 1..."],
                ["Stock 2", "The answer to your question 2..."],
                ["Stock 3", "The answer to your question 3..."],
        ]
        for name, body in stock_responses:
            StockResponse.objects.create(name=name, body=body)

        res = self.client.get("/correspondence/stock_responses.json")
        self.assertEquals(res.status_code, 403)

        self.loginAs("reader")
        res = self.client.get("/correspondence/stock_responses.json")
        self.assertEquals(res.status_code, 403)

        self.loginAs("moderator")
        res = self.client.get("/correspondence/stock_responses.json")
        self.assertEquals(res.status_code, 200)
        self.assertEquals(json.loads(res.content), {
            'results': [
                {'id': 3, 'name': "Stock 3", 'body': "The answer to your question 3..."},
                {'id': 2, 'name': "Stock 2", 'body': "The answer to your question 2..."},
                {'id': 1, 'name': "Stock 1", 'body': "The answer to your question 1..."},
            ]
        })

class TestLetterGeneration(LiveServerTestCase, BtbLoginTestCase):
    def setUp(self):
        super(TestLetterGeneration, self).setUp()
        self.sender = User.objects.get(username='moderator')
        self.recipient = User.objects.get(username='author')
        self.org = self.org
        site = Site.objects.get_current()
        site.domain = self.live_server_url.replace("http://", "")
        site.save()

    def create_letter(self, **kwargs):
        args = {
            'sender': self.sender,
            'recipient': self.recipient,
            'org': self.recipient.organization_set.all()[0],
        }
        args.update(kwargs)
        return Letter.objects.create(**args)

    def create_document(self, **kwargs):
        src = os.path.join(os.path.dirname(__file__), "..", "media", "test", "src", "one-pager.pdf")
        args = {
            'author': kwargs.get('author', self.recipient),
            'uploader': kwargs.get('uploader', self.sender),
            'org': kwargs.get('org', self.org),
        }
        scan = Scan(**args)
        with open(src, 'rb') as fh:
            scan.pdf.save("one-pager.pdf", File(fh))
        split_scan(scan=scan)

        doc = Document.objects.create(
            title="One-pager",
            type='post',
            author=scan.author,
            editor=scan.uploader,
            scan=scan,
        )
        dp = DocumentPage.objects.create(document=doc, order=0,
                scan_page=scan.scanpage_set.all()[0])
        doc.highlight_transform = json.dumps({
            "document_page_id": dp.id,
            "crop": [62, 65.5, 583, 308.5],
        })
        if kwargs.get('status'):
            doc.status = kwargs['status']
        doc.save()
        update_document_images(document=doc)
        return doc

    def assertPageContains(self, page, text, contains=True):
        # pyPDF kills whitespace in pdfs -- so compare the text with all
        # whitespace removed.
        self.assertEquals(contains, re.sub('\s', '', text) in page.extractText())

    def assertPageNotContains(self, page, text):
        return self.assertPageContains(page, text, False)

    def test_plain_letter(self):
        letter = self.create_letter(type='letter', body='Rock on')
        letter.get_file()
        with open(letter.file.path) as fh:
            reader = PdfFileReader(fh)
            self.assertEquals(reader.getNumPages(), 1)
            page = reader.getPage(0)
            self.assertPageContains(page, self.org.mailing_address)
            self.assertPageContains(page, letter.body)
            self.assertPageContains(page, "Kind Regards, " + letter.sender.profile.display_name)
        letter.delete()
    
    def test_send_anonymously(self):
        letter = self.create_letter(type='letter', body='Rock on', send_anonymously=True)
        letter.get_file()
        with open(letter.file.path) as fh:
            reader = PdfFileReader(fh)
            page = reader.getPage(0)
            self.assertPageContains(page, "Kind Regards, {0} staff".format(letter.org.name))
            self.assertPageNotContains(page, letter.sender.profile.display_name)
        letter.delete()

    def test_send_postcard(self):
        letter = self.create_letter(type='letter', body='Rock on', is_postcard=True)
        letter.get_file()
        self.assertTrue(letter.file.path.endswith(".jpg"))
        self.assertTrue(letter.file.size > 0)
        letter.delete()

    def test_consent_form(self):
        letter = self.create_letter(type='consent_form')
        letter.get_file()
        with open(letter.file.path) as fh:
            reader = PdfFileReader(fh)
            self.assertEquals(reader.getNumPages(), 10)
            page = reader.getPage(0)
            # Cover letter
            self.assertPageContains(reader.getPage(0), "like to invite you to join")
            # page 1 is blank

            # Intro packet
            self.assertPageContains(reader.getPage(2), "is a blogging platform")
            self.assertPageContains(reader.getPage(3), "Everyone with an Internet connection")
            self.assertPageContains(reader.getPage(4), "in your real name")
            self.assertPageContains(reader.getPage(5), "as legibly as possible")

            # License agreement -- text extraction doesn't work, don't know why.
            #self.assertPageContains(reader.getPage(6), "YOUR COPY TO KEEP")
            #self.assertPageContains(reader.getPage(7), "Termination")
            #self.assertPageContains(reader.getPage(8), "RETURN THIS COPY")
            #self.assertPageContains(reader.getPage(9), "Request for Removal")
        letter.delete()

    def test_consent_form_with_custom_pdf(self):
        pass

    def test_signup_complete(self):
        letter = self.create_letter(type='signup_complete')
        letter.get_file()
        with open(letter.file.path) as fh:
            reader = PdfFileReader(fh)
            self.assertEquals(reader.getNumPages(), 2)
            page = reader.getPage(0)
            self.assertPageContains(page, """Please remember that these
                exchanges, like all information published""")
            page = reader.getPage(1)
            self.assertPageContains(page, "Kind Regards, {0} staff".format(letter.org.name))
        letter.delete()

    def test_first_post(self):
        doc = self.create_document(status='published')
        letter = self.create_letter(type='first_post', recipient=doc.author)
        letter.get_file()
        with open(letter.file.path) as fh:
            reader = PdfFileReader(fh)
            self.assertEquals(reader.getNumPages(), 2)
            self.assertPageContains(reader.getPage(0), "how it looks on the Internet")
            # pyPdf Can't extract text from the wkhtmltopdf printed page..
            #self.assertPageContains(reader.getPage(1), doc.author.profile.display_name)
        doc.scan.full_delete()
        letter.delete()

    def test_printout(self):
        doc = self.create_document(status='published')
        letter = self.create_letter(type='printout', document=doc)
        letter.get_file()
        with open(letter.file.path) as fh:
            reader = PdfFileReader(fh)
            self.assertEquals(reader.getNumPages(), 1)
        doc.scan.full_delete()
        letter.delete()

    def test_comments(self):
        doc = self.create_document(status='published')
        comment = Comment.objects.create(
            user=User.objects.get(username='reader'),
            comment="Wow. So Doge.",
            document=doc
        )
        letter = self.create_letter(type='comments')
        letter.comments.add(comment)
        letter.get_file()
        with open(letter.file.path) as fh:
            reader = PdfFileReader(fh)
            self.assertEquals(reader.getNumPages(), 2)
            self.assertPageContains(reader.getPage(0), "printout of recent comments")
        doc.scan.full_delete()
        letter.delete()

    def test_waitlist(self):
        letter = self.create_letter(type='waitlist', is_postcard=True)
        letter.get_file()
        self.assertTrue(letter.file.path.endswith(".jpg"))
        self.assertTrue(letter.file.size > 0)
        letter.delete()

    def test_returned_original(self):
        doc = self.create_document(status='unknown')
        letter = self.create_letter(type='returned_original', document=doc)
        letter.get_file()
        with open(letter.file.path) as fh:
            reader = PdfFileReader(fh)
            self.assertEquals(reader.getNumPages(), 1)
            self.assertPageContains(reader.getPage(0), "Thanks for your submission")
        doc.scan.full_delete()
        letter.delete()

    def test_refused_original(self):
        doc = self.create_document(status='unknown')
        letter = self.create_letter(type='refused_original', document=doc)
        letter.get_file()
        with open(letter.file.path) as fh:
            reader = PdfFileReader(fh)
            self.assertEquals(reader.getNumPages(), 1)
            self.assertPageContains(reader.getPage(0), "we cannot publish")
        doc.scan.full_delete()
        letter.delete()

    def test_custom_pdf(self):
        src = os.path.join(os.path.dirname(__file__), "..", "media", "test", "src", "ex-prof-posts.pdf")
        letter = self.create_letter(type='letter')
        upload_to = os.path.join(settings.MEDIA_ROOT, letter.custom_pdf.field.upload_to)
        if not os.path.exists(upload_to):
            os.makedirs(upload_to)
        dest = os.path.join(upload_to, os.path.basename(src))
        shutil.copy(src, dest)
        letter.custom_pdf = os.path.relpath(dest, settings.MEDIA_ROOT)
        letter.save()
        letter.get_file()
        with open(letter.file.path, 'rb') as fh1:
            with open(letter.custom_pdf.path, 'rb') as fh2:
                self.assertEquals(fh1.read(), fh2.read())
        os.remove(letter.custom_pdf.path)
        letter.delete()

class TestNeededLetters(TestCase):
    def setUp(self):
        self.mod = User.objects.create(username='moderator')
        self.org = Organization.objects.create(name='org')
        self.org.moderators.add(self.mod)
        self.reader = User.objects.create(username='reader')

    def create_user(self, **kwargs):
        user = User.objects.create(username=kwargs.get('username', 'testauthor'))
        user.profile.blogger = kwargs.get('blogger', True)
        user.profile.managed = kwargs.get('managed', True)
        user.profile.consent_form_received = kwargs.get('consent_form_received', True)
        user.profile.save()
        self.org.members.add(user)
        if kwargs.get('signup_complete_sent'):
            Letter.objects.create(recipient=user, sender=self.mod,
                    type='signup_complete', sent=datetime.datetime.now())
        return user

    def create_doc(self, author, **kwargs):
        return Document.objects.create(
                author=author,
                type=kwargs.get('type', 'post'),
                editor=self.mod,
                status=kwargs.get('status', 'published'))

    def send_first_post(self, doc):
        Letter.objects.create(type='first_post', recipient=doc.author,
                sender=doc.editor, document=doc, sent=datetime.datetime.now())

    def assertNeededLetters(self, **kwargs):
        expected = {
            'consent_form': Profile.objects.none(),
            'signup_complete': Profile.objects.none(),
            'first_post': Profile.objects.none(),
            'comments': Profile.objects.none(),
            'waitlist': Profile.objects.none(),
            'enqueued': Letter.objects.none(),
            'comment_removal': CommentRemoval.objects.none(),
        }
        expected.update(kwargs)
        actual = needed_letters(self.mod)
        for key, val in expected.iteritems():
            try:
                self.assertEquals(set(list(val)), set(list(actual[key])))
            except AssertionError:
                print key
                raise

    def test_needs_waitlist_postcard(self):
        user = self.create_user(consent_form_received=False)
        self.assertNeededLetters(waitlist=[user.profile], consent_form=[user.profile])

        # Inactive users get nothing.
        user.is_active = False
        user.save()
        self.assertNeededLetters()

        # Unmanaged users get nothing.
        user.is_active = True
        user.save()
        user.profile.managed = False
        user.profile.save()
        self.assertNeededLetters()

        # Non-bloggers get nothing
        user.profile.managed = True
        user.profile.blogger = False
        user.profile.save()
        self.assertNeededLetters()

    def test_needs_consent_form(self):
        user = self.create_user(consent_form_received=False)
        letter = Letter.objects.create(type='waitlist', is_postcard=True,
                recipient=user, sender=self.mod, sent=datetime.datetime.now())
        self.assertNeededLetters(consent_form=[user.profile])

        
        # Waitlist should appear in 'enqueued' if it isn't sent yet.
        letter.sent = None
        letter.save()
        self.assertNeededLetters(consent_form=[user.profile], enqueued=[letter])

    def test_needs_signup_complete(self):
        user = self.create_user()
        self.assertNeededLetters(signup_complete=[user.profile])

    def test_needs_first_post(self):
        user = self.create_user(signup_complete_sent=True)
        doc = self.create_doc(user)
        self.assertNeededLetters(first_post=[user.profile])

        # Counts 'profile' documents as first posts.
        doc.type = 'profile'
        doc.save()
        self.assertNeededLetters(first_post=[user.profile])

        self.send_first_post(doc)
        self.assertNeededLetters()

    def test_needs_comments(self):
        user = self.create_user(signup_complete_sent=True)
        doc = self.create_doc(user)
        self.send_first_post(doc)
        comment = Comment.objects.create(document=doc, comment="blah", user=self.reader)
        self.assertNeededLetters(comments=[user.profile])

        # Doesn't count removed comments.
        comment.removed = True
        comment.save()
        self.assertNeededLetters()

        # Doesn't fire on unpublished posts.
        doc.status = 'unknown'
        doc.save()
        comment.removed = False
        comment.save()
        self.assertNeededLetters()

        # Doesn't include self-replies.
        comment.delete()
        doc.status = 'published'
        doc.save()
        self_reply = Document.objects.create(
                author=doc.author,
                editor=doc.editor,
                in_reply_to=doc.reply_code,
                status='published')
        self.assertEquals(len(Comment.objects.filter(comment_doc=self_reply)), 1)
        self.assertNeededLetters()

    def test_needs_enqueued(self):
        user = self.create_user(signup_complete_sent=True)
        letter = Letter.objects.create(type='letter', recipient=user, sender=self.mod)
        self.assertNeededLetters(enqueued=[letter])

        # Unlike auto-generated types, enqueued letters go out regardless of
        # inactive/blogger/managed/consent status.

        # Inactive still get them.
        user.is_active = False
        user.save()
        self.assertNeededLetters(enqueued=[letter])

        # Unmanaged users do too.
        user.is_active = True
        user.save()
        user.profile.managed = False
        user.profile.save()
        self.assertNeededLetters(enqueued=[letter])

        # Non-bloggers do too.
        user.profile.managed = True
        user.profile.blogger = False
        user.profile.save()
        self.assertNeededLetters(enqueued=[letter])

        # Unconsented do too.
        user.profile.consent_form_received = False
        user.profile.save()
        self.assertNeededLetters(enqueued=[letter])

        # But not lost_contact..
        user.profile.lost_contact = True
        user.profile.save()
        self.assertNeededLetters()

        # Already sent, then we neen't send it again.
        user.profile.lost_contact = False
        user.profile.save()
        letter.sent = datetime.datetime.now()
        letter.save()
        self.assertNeededLetters()

    def test_needs_comment_removal(self):
        user = self.create_user(signup_complete_sent=True)
        doc = self.create_doc(user)
        self.send_first_post(doc)
        comment = Comment.objects.create(document=doc, comment="blah", user=self.reader,
                removed=True)
        cr = CommentRemoval.objects.create(comment=comment,
                post_author_message="you got a thingy we removed")
        self.assertNeededLetters(comment_removal=[cr])

        # No letter if cr.post_author_message is empty.
        cr.post_author_message = ""
        cr.save()
        self.assertNeededLetters()

        # Already sent.
        cr.post_author_message = "foo"
        cr.save()
        letter = Letter.objects.create(type='comment_removal', recipient=user,
                sender=self.mod, sent=datetime.datetime.now())
        letter.comments.add(comment)
        self.assertNeededLetters()

