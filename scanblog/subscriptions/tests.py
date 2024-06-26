import re
import datetime

from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.core import mail
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.sites.models import Site
from django.test.utils import override_settings

from btb.tests import BtbMailTestCase
from profiles.models import Organization
from subscriptions.models import (Subscription, NotificationBlacklist, CommentNotificationLog,
    UserNotificationLog, DocumentNotificationLog, MailingListInterest)
from scanning.models import Document, Transcription, TranscriptionRevision
from comments.models import Comment
from annotations.models import Tag, ReplyCode
from campaigns.models import Campaign

@override_settings(DISABLE_NOTIFICATIONS=False, DISABLE_ADMIN_NOTIFICATIONS=False)
class TestSubscriptions(BtbMailTestCase):
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
        doc = Document.objects.create(author=self.author, 
                editor=self.editor, status="published")
        self.assertEquals(Subscription.objects.count(), 0)

        comment = Comment.objects.create(comment="test", 
                document=doc, user=self.commenter)
        self.assertOutboxIsEmpty()
        self.clear_outbox()

        self.assertEquals(Subscription.objects.count(), 1)
        s = Subscription.objects.get()
        self.assertEquals(s.document, doc)
        self.assertEquals(s.subscriber, self.commenter)

        # No notification to commenter for their own comments, even when
        # subscribed.  No notification for admin unless comment is spammy (has
        # links).
        second_comment = Comment.objects.create(comment="test2",
                document=doc, user=self.commenter)
        self.assertOutboxIsEmpty()
        self.clear_outbox()

        # Notification for subscribed comment.
        third_comment = Comment.objects.create(comment="test3",
                document=doc, user=self.commenter2)
        self.assertOutboxContains([
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
        
    def test_multiple_comment_notification(self):
        CommentNotificationLog.objects.all().delete()
        doc = Document.objects.create(author=self.author, editor=self.editor, status="published")
        self.clear_outbox()
        comment1 = Comment.objects.create(comment="yah", user=self.commenter, document=doc)
        comment2 = Comment.objects.create(comment="huh", user=self.commenter2, document=doc)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(CommentNotificationLog.objects.count(), 1)
        self.clear_outbox()
        comment2.comment = "huh edited"
        comment2.save()
        self.assertEquals(len(mail.outbox), 0)
        self.assertEquals(CommentNotificationLog.objects.count(), 1)

    def test_documentless_comment_saving(self):
        self.clear_outbox()
        doc = Document.objects.create(author=self.author, editor=self.editor, status="published")
        Subscription.objects.create(author=self.author, subscriber=self.commenter)
        comment = Comment.objects.create(comment="A fine comment",
                user=self.commenter2,
                document=doc)
        comment = Comment.objects.create(comment="An admin mistake", user=self.editor)
        self.assertEquals(mail.outbox, [])

    def test_moderator_notification_on_content_with_links(self):
        # Nothing with no link.
        self.clear_outbox()
        doc = Document.objects.create(author=self.author, editor=self.editor, status="published")
        comment = Comment.objects.create(comment="No link",
                user=self.commenter,
                document=doc)
        TranscriptionRevision.objects.create(
                transcription=Transcription.objects.create(document=doc),
                editor=self.commenter,
                body="No link")
        self.assertEquals(len(mail.outbox), 0)

        # Notification with non-self links
        for protocol in ("http", "https"):
            self.clear_outbox()
            doc = Document.objects.create(author=self.author, editor=self.editor,
                    status="published")
            comment = Comment.objects.create(
                    comment="{0}://advertiser.com".format(protocol),
                    user=self.commenter,
                    document=doc)
            self.assertEquals(len(mail.outbox), 1)

            self.clear_outbox()
            TranscriptionRevision.objects.create(
                    transcription=Transcription.objects.create(document=doc),
                    editor=self.commenter,
                    body="{0}://advertiser.com".format(protocol))
            self.assertEquals(len(mail.outbox), 1)

        # Nothing with self links.
        for protocol in ("http", "https"):
            self.clear_outbox()
            doc = Document.objects.create(author=self.author, editor=self.editor,
                    status="published")

            comment = Comment.objects.create(
                    comment="{0}://{1}/blogs/101/".format(
                        protocol,
                        Site.objects.get_current().domain
                    ),
                    user=self.commenter,
                    document=doc)

            TranscriptionRevision.objects.create(
                    transcription=Transcription.objects.create(document=doc),
                    editor=self.commenter,
                    body="{0}://{1}/blogs/101.com".format(
                        protocol,
                        Site.objects.get_current().domain
                    ))

            self.assertEquals(len(mail.outbox), 0)

    def test_no_flooding_of_users_documents(self):
        """
        Ensure that notifications are not sent too quickly to users, even if
        they are scheduled to receive them.
        """
        self.clear_outbox()
        Subscription.objects.create(author=self.author, subscriber=self.commenter)
        doc1 = Document.objects.create(
                author=self.author, editor=self.editor, status="published")
        doc2 = Document.objects.create(
                author=self.author, editor=self.editor, status="published")
        doc3 = Document.objects.create(
                author=self.author, editor=self.editor, status="published")

        # They only get one email, but we log 3 notifications, so they won't
        # get those flood-y ones in the future either.
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to, [self.commenter.email])
        self.clear_outbox()
        self.assertEquals(DocumentNotificationLog.objects.filter(
            recipient=self.commenter).count(), 3)

        # Change the date of the UserNotificationLog, and we should get a new notice.
        log = self.commenter.usernotificationlog_set.all()[0]
        log.date = log.date - datetime.timedelta(seconds=31*60)
        log.save()

        Document.objects.create(author=self.author, editor=self.editor, status="published")
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to, [self.commenter.email])
        self.clear_outbox()
        self.assertEquals(self.commenter.usernotificationlog_set.count(), 2)

        # Comments won't produce logs in this interval either.
        # Add a comment by 'user', which should auto-subscribe them to comments on this doc.
        Comment.objects.create(user=self.commenter, document=doc1, comment="Woo")
        # Add a comment from someone else, which would create a notice if they
        # weren't flood-blocked.
        Comment.objects.create(user=self.commenter2, document=doc1, comment="Waa")
        self.assertEquals(len(mail.outbox), 0)

        # Non flood-blocked users should still get comment notices though.
        Comment.objects.create(user=self.commenter, document=doc1, comment="Wor")
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to, [self.commenter2.email])
        self.clear_outbox()

        # If the latest log is old enough, and comments will again fire notices.
        log = self.commenter.usernotificationlog_set.all()[0]
        log.date = log.date - datetime.timedelta(seconds=31*60)
        log.save()

        Comment.objects.create(user=self.editor, document=doc1, comment="Wam")
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to, [self.commenter.email])

class TestMailingListInterest(TestCase):
    url = reverse("subscriptions.mailing_list_interest")

    def test_gets_mailing_list_interest_view(self):
        res = self.client.get(self.url)
        self.assertEquals(res.status_code, 200)
        self.assertTrue("Are you interested in volunteering?" in res.content)

    def test_posts_mailing_list_interest(self):
        res = self.client.post(self.url, {
            'email': 'test@example.com',
            'details': '',
        }, follow=True)
        self.assertEquals(res.status_code, 200)
        self.assertTrue("Thanks for your interest" in res.content)
        self.assertEquals(MailingListInterest.objects.count(), 1)
        m = MailingListInterest.objects.get()
        self.assertEquals(m.email, 'test@example.com')
        self.assertEquals(m.details, '')
        self.assertEquals(m.allies, False)
        self.assertEquals(m.announcements, False)
        self.assertEquals(m.volunteering, False)

