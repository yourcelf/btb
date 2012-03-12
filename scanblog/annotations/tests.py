import json

from django.test import TestCase

from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from scanning.models import Document
from comments.models import Comment
from annotations.models import ReplyCode
from profiles.models import Organization
from btb.tests import BtbMailTestCase

class ReplyCodesTest(TestCase):
    def setUp(self):
        self.author = User.objects.create(username="author")
        self.editor = User.objects.create(username="editor")
        self.editor.set_password("editor")
        self.editor.save()
        self.editor.groups.add(Group.objects.get(name='moderators'))
        self.org = Organization.objects.create(name="org")
        self.org.members.add(self.author)
        self.org.moderators.add(self.editor)

    def test_reply_code_creation(self):
        orig = Document.objects.create(author=self.author, editor=self.editor)
        self.assertTrue(bool(orig.reply_code))

    def test_simple_reply(self):
        # Create original.  No comments.
        orig = Document.objects.create(author=self.author, editor=self.editor, status="published")
        self.assertEquals(orig.comments.count(), 0)

        # Create a reply.
        reply = Document.objects.create(author=self.author, editor=self.author)
        reply.in_reply_to = orig.reply_code
        reply.status = "published"
        reply.save()

        # A comment was automatically created for the reply.
        self.assertEquals(orig.comments.count(), 1)
        self.assertEquals(orig.comments.get().comment_doc, reply)

        # Unpublishing the reply 'removes' the comment.
        reply.status = "unknown"
        reply.save()
        self.assertEquals(orig.comments.filter(removed=False).count(), 0)
        self.assertEquals(orig.comments.filter(removed=True).count(), 1)

        # Republishing un-removes the comment.
        reply.status = "published"
        reply.save()
        self.assertEquals(orig.comments.filter(removed=True).count(), 0)
        self.assertEquals(orig.comments.filter(removed=False).count(), 1)

        # Deleting deletes the comment too.
        reply.delete()
        self.assertEquals(orig.comments.count(), 0)

    def test_grep_reply_code(self):
        """
        Test the AJAX methods for looking up reply codes.
        """

        url = "/annotations/reply_codes.json"
        # Nonexistent code.
        c = self.client
        self.assertTrue(c.login(username="editor", password="editor"))
        res = c.get(url)
        self.assertEquals(res.status_code, 404)
        res = c.get(url, {'code': 'asdf'})
        self.assertEquals(res.status_code, 200)
        self.assertEquals(json.loads(res.content)['results'], [])

        # Existent code
        orig = Document.objects.create(author=self.author, editor=self.editor, status="published")
        res = c.get(url, {'code': orig.reply_code.code})
        self.assertEquals(json.loads(res.content)['results'], [orig.reply_code.to_dict()])
        res = c.get(url, {'code': orig.reply_code.code, 'document': 1})
        self.assertEquals(json.loads(res.content)['results'], [orig.reply_code.doc_dict()])

        # Code without document
        rc = ReplyCode.objects.create()
        res = c.get(url, {'code': rc.code})
        self.assertEquals(json.loads(res.content)['results'], [rc.to_dict()])
        res = c.get(url, {'code': rc.code, 'document': 1})
        self.assertEquals(res.status_code, 200)
        self.assertEquals(json.loads(res.content)['results'], [])

class FlagTest(BtbMailTestCase):
    def setUp(self, *args, **kwargs):
        super(FlagTest, self).setUp(*args, **kwargs)
        self.author = User.objects.create(username="author")
        self.author.profile.managed = True
        self.author.profile.save()
        self.editor = User.objects.create(username="editor")
        self.editor.set_password("editor")
        self.editor.save()
        self.editor.groups.add(Group.objects.get(name='moderators'))
        self.reader = User.objects.create(username="reader")
        self.reader.groups.add(Group.objects.get(name='readers'))
        self.reader.set_password("reader")
        self.reader.save()
        self.org = Organization.objects.create(name="org")
        self.org.members.add(self.author)
        self.org.moderators.add(self.editor)

    def test_flag_notifications(self):
        c = self.client
        doc = Document.objects.create(author=self.author, editor=self.editor, status="published")
        self.assertTrue(c.login(username="reader", password="reader"))

        # Document flag
        url = reverse("scanning.flag_document", args=[doc.pk])
        res = c.post(url, {'reason': 'oh my!!'})
        self.assertEquals(res.status_code, 302)
        self.assertOutboxContains(["%sContent flagged" % self.admin_subject_prefix])
        self.clear_outbox()

        # Comment
        comment = Comment.objects.create(document=doc, user=self.reader)
        self.assertTrue(c.login(username="reader", password="reader"))
        self.assertOutboxContains(["%sNew comment" % self.admin_subject_prefix])
        self.clear_outbox()

        # Comment flag
        url = reverse("comments.flag_comment", args=[comment.pk])
        res = c.post(url, {'reason': 'oh my!!'})
        self.assertEquals(res.status_code, 302)
        self.assertOutboxContains(["%sContent flagged" % self.admin_subject_prefix])
