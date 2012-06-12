import re

from django.contrib.auth.models import User, Group
from django.core import mail
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.sites.models import Site

from btb.tests import BtbMailTestCase
from profiles.models import Organization
from subscriptions.models import Subscription, NotificationBlacklist
from scanning.models import Document
from comments.models import Comment
from annotations.models import Tag, ReplyCode
from campaigns.models import Campaign

class TestSubscriptions(BtbMailTestCase):
    fixtures = ["initial_data.json"]
    def setUp(self):
        super(TestSubscriptions, self).setUp()
        self.editor = User.objects.create(username='editor')
        self.editor.set_password('editor')
        self.editor.save()
        self.editor.groups.add(Group.objects.get(name='moderators'))
        self.author = User.objects.create(username='author')
        self.author.profile.blogger = True
        self.author.profile.managed = True
        self.author.profile.consent_form_received = True
        self.author.profile.save()
        self.org = Organization.objects.create(name='org')
        self.org.members.add(self.author)
        self.org.moderators.add(self.editor)

        self.commenter = User.objects.create(
                username='commenter', 
                email="test@example.com"
            )
        self.commenter.set_password("commenter")
        self.commenter.save()
        self.commenter2 = User.objects.create(
                username="commenter2",
                email="test2@example.com"
            )

    def test_auto_subscribe_and_comment_notifications(self):
        """
        Note: Must have the settings:

            DISABLE_NOTIFICATIONS = False 
            DISABLE_ADMIN_NOTIFICATIONS = False

        at the time of subscription model module loading for this test to work.
        """
        doc = Document.objects.create(author=self.author, 
                editor=self.editor, status="published")
        self.assertEquals(Subscription.objects.count(), 0)

        comment = Comment.objects.create(comment="test", 
                document=doc, user=self.commenter)
        self.assertOutboxContains(["%sNew comment" % self.admin_subject_prefix])
        self.clear_outbox()

        self.assertEquals(Subscription.objects.count(), 1)
        s = Subscription.objects.get()
        self.assertEquals(s.document, doc)
        self.assertEquals(s.subscriber, self.commenter)

        # No notification to commenter for their own comments, even when
        # subscribed, but yes notification for admin.
        second_comment = Comment.objects.create(comment="test2",
                document=doc, user=self.commenter)
        self.assertOutboxContains(["%sNew comment" % self.admin_subject_prefix])
        self.clear_outbox()

        # Notification for subscribed comment.
        third_comment = Comment.objects.create(comment="test3",
                document=doc, user=self.commenter2)
        self.assertOutboxContains([
            "%sNew comment" % self.admin_subject_prefix,
            "%sNew reply" % self.user_subject_prefix,
        ])
        self.clear_outbox()

    def test_author_notifications(self):
        """
        Test notifications for subscribers to authors.
        """
        Subscription.objects.create(subscriber=self.commenter, author=self.author) 

        doc = Document.objects.create(author=self.author,
                editor=self.editor)
        # No notification until published.
        self.assertOutboxIsEmpty()

        doc.status = "published"
        doc.save()

        self.assertOutboxContains(["%sNew post" % self.user_subject_prefix])
        self.clear_outbox()

    def test_tag_notifications(self):
        """
        Test notifications for subscribers to tags.
        """
        tag = Tag.objects.create(name="featured")
        Subscription.objects.create(subscriber=self.commenter, tag=tag)
        doc = Document.objects.create(author=self.author, editor=self.editor, status="published")
        doc.tags.add(tag)
        doc.save()

        self.assertOutboxContains(["%sNew post" % self.user_subject_prefix])
        self.clear_outbox()

    def test_org_notifications(self):
        """
        Test notifications for subscribers to organizations.
        """
        Subscription.objects.create(subscriber=self.commenter, organization=self.org)
        doc = Document.objects.create(author=self.author, 
                editor=self.editor, status="published")
        self.assertOutboxContains(["%sNew post" % self.user_subject_prefix])
        self.clear_outbox()

    def test_campaign_notifications(self):
        reply_code = ReplyCode.objects.create(code='test-campaign')
        campaign = Campaign.objects.create(slug='test', title='', body='',
                public=True, 
                reply_code=reply_code)
        Subscription.objects.create(subscriber=self.commenter, campaign=campaign)
        doc = Document.objects.create(author=self.author, editor=self.editor,
                status="published", in_reply_to=reply_code)
        self.assertOutboxContains(["%sNew post" % self.user_subject_prefix])
        self.clear_outbox()

    def test_reply_coded_comment_notifications(self):
        """
        Test notifications for document replies to comments.
        """
        doc = Document.objects.create(author=self.author, editor=self.editor, status="published")
        comment = Comment.objects.create(user=self.commenter, document=doc)
        self.clear_outbox()
        reply = Document.objects.create(author=self.author, editor=self.editor,
                status="published", in_reply_to=doc.reply_code)
        # No admin notification for document.
        self.assertOutboxContains(["%sNew reply" % self.user_subject_prefix])

    def test_no_duplicate_document_notifications(self):
        """
        Ensure that you don't get duplicated more than once for a document,
        even if you're multiply subscribed to it.
        """
        tag = Tag.objects.create(name="featured")
        campaign = Campaign.objects.create(slug='test', title='', body='',
                reply_code=ReplyCode.objects.create(code='test-campaign'))
        Subscription.objects.create(subscriber=self.commenter, author=self.author)
        Subscription.objects.create(subscriber=self.commenter, organization=self.org)
        Subscription.objects.create(subscriber=self.commenter, tag=tag)
        Subscription.objects.create(subscriber=self.commenter, campaign=campaign)
        doc = Document.objects.create(author=self.author, editor=self.editor,
                in_reply_to=campaign.reply_code)
        doc.tags.add(tag)
        doc.status = "published"
        doc.save()

        # Only one, despite triple subscription
        self.assertOutboxContains(["%sNew post" % self.user_subject_prefix])
        self.clear_outbox()

        doc.save()
        doc.save()
        doc.save()

        # and no more.
        self.assertOutboxIsEmpty()

    def test_unsubscribe(self):
        """
        Test the HTTP method which unsubscribes you completely from all email
        notifications.  This is included in the link at the bottom of emails.
        """
        c = self.client
        c.login(username="commenter", password="commenter")
        res = c.get(reverse("subscriptions.unsubscribe"))
        self.assertNoNotificationsFor(self.commenter)

    def test_unsubscribe_link(self):
        c = self.client
        c.logout()
        doc = Document.objects.create(author=self.author, editor=self.editor, 
                status="published", type="post")
        # Create a subscription...
        Comment.objects.create(user=self.commenter, comment="foo", document=doc)
        # ... trigger a notification ...
        Comment.objects.create(user=self.commenter2, comment="foo", document=doc)
        for msg in mail.outbox:
            if self.commenter.email in msg.to:
                body = msg.message().get_payload(None, True)
                break
        else:
            self.fail("Expected notification for %s, got none." % self.commenter.email)

        self.clear_outbox()

        match = re.search("^<https?://[^/]*(/r/.*)>$", body, re.MULTILINE)
        if match:
            link = match.group(1)
            res = c.get(link, follow=True)
            self.assertNoNotificationsFor(self.commenter)
        else:
            self.fail("Unsubscribe link not found.")

    def test_blacklist(self):
        """
        Test the NotificationBlacklist, a table of email addresses to which we
        never send any email under any circumstances.
        """
        NotificationBlacklist.objects.create(email=self.commenter.email)
        self.assertNoNotificationsFor(self.commenter)

    def assertNoNotificationsFor(self, commenter):
        """
        Assert that there are no email notifications for any of the
        notification types for the given user.
        """
        tag = Tag.objects.create(name="featured")
        Subscription.objects.create(subscriber=commenter, author=self.author)
        Subscription.objects.create(subscriber=commenter, organization=self.org)
        Subscription.objects.create(subscriber=commenter, tag=tag)
        doc = Document.objects.create(author=self.author, editor=self.editor)
        doc.tags.add(tag)
        doc.status = "published"
        doc.save()

        # Triple notification none!
        self.assertEquals(mail.outbox, [])

        # Nor comments!
        Comment.objects.create(document=doc, user=commenter)
        otherCommenter = User.objects.create(username="blah")
        Comment.objects.create(document=doc, user=otherCommenter)

        # (just outbox)
        self.assertOutboxContains(['%sNew comment' % self.admin_subject_prefix] * 2)

    def test_comment_notification_escaping(self):
        doc = Document.objects.create(author=self.author, editor=self.editor, status="published")
        comment = Comment.objects.create(comment="yah", user=self.commenter, document=doc)
        self.clear_outbox()
        text = """Isn't that & that nice. >.<"""
        comment = Comment.objects.create(comment=text, user=self.commenter2, document=doc)

        for msg in mail.outbox:
            self.assertTrue(text in unicode(msg.message()))

    def test_visitor_profile(self):
        doc = Document.objects.create(
                author=self.commenter, 
                editor=self.commenter,
                type="profile")
        self.assertOutboxContains(["%sProfile uploaded" % self.admin_subject_prefix])

    def test_unmanaged_author_notifications(self):
        self.author.profile.managed = False
        self.author.profile.save()
        doc = Document.objects.create(
                author=self.author, 
                editor=self.author, 
                type="post",
                body="This is my fun body text", 
                title="This is the title.",
                status="published")

        msg = mail.outbox.pop()
        self.assertEquals(msg.subject, "%sNew post" % self.admin_subject_prefix)
        self.assertEquals(msg.to, [m[1] for m in settings.MANAGERS])
        self.assertTrue("This is my fun body text" in msg.message().get_payload(None, True))
        self.assertEquals(mail.outbox, [])
        

