import datetime
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from scanning.models import Document
from annotations.models import Tag
from comments.models import Comment
from profiles.models import Organization, Affiliation
from campaigns.models import Campaign

from notification import models as notification

# Create your models here.
class Subscription(models.Model):
    subscriber = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="subscriptions")
    document = models.ForeignKey(Document, related_name="subscriptions",
            blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="author_subscriptions",
            blank=True, null=True)
    tag = models.ForeignKey(Tag, related_name="tag_subscriptions",
            blank=True, null=True)
    organization = models.ForeignKey(Organization, related_name="organization_subscriptions",
            blank=True, null=True)
    campaign = models.ForeignKey(Campaign, related_name="organization_subscriptions",
            blank=True, null=True)
    affiliation = models.ForeignKey(Affiliation, related_name="affiliation_subscriptions",
            blank=True, null=True)

    def __unicode__(self):
        return "%s -> %s" % (self.subscriber, 
            (self.document or self.author or self.tag or self.campaign or self.affiliation))

    class Meta:
        ordering = ['tag', 'author', 'document', 'campaign', 'affiliation']

class DocumentNotificationLog(models.Model):
    """
    Log notifications of documents, so that we only send once per document,
    even if the user is multiply subscribed (e.g. to featured posts as well as
    posts by an author).
    """
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL)
    document = models.ForeignKey(Document)

    def __unicode__(self):
        return "%s -> %s" % (self.document, self.recipient)

class CommentNotificationLog(models.Model):
    """
    Log notifications of comments, so that we only send once per comment,
    even if the comment is edited.
    """
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL)
    comment = models.ForeignKey(Comment)

    def __unicode__(self):
        return "%s -> %s" % (self.comment, self.recipient)

class NotificationBlacklist(models.Model):
    """
    Any email in this list will never be sent a notification.  For abuse
    prevention.
    """
    email = models.EmailField()
    def __unicode__(self):
        return self.email

class UserNotificationLog(models.Model):
    """
    Log of each notification sent to a user, used for throttling of
    notifications.
    """
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL)
    date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s -> %s" % (self.recipient, self.date)

    class Meta:
        ordering = ['-date']

class MailingListInterest(models.Model):
    email = models.EmailField(max_length=254)
    volunteering = models.BooleanField(
            default=False,
            help_text="Are you interested in volunteering?")
    allies = models.BooleanField(
            default=False,
            help_text="Are you interested in joining with Between the Bars in campaigns?")
    announcements = models.BooleanField(
            default=False,
            help_text="Are you interested in announcements about new projects and features?")
    details = models.TextField(blank=True,
            help_text="Tell us more about your interests, if you like.")

    def __unicode__(self):
        return self.email

def send_notices(recipients, *args):
    """
    Send notices, but throttled by the UserNotificationLog.
    """
    cutoff = datetime.datetime.now() - datetime.timedelta(seconds=30*60)
    new_recipients = []
    for recipient in recipients:
        if UserNotificationLog.objects.filter(
                date__gte=cutoff, recipient=recipient).exists():
            continue
        else:
            UserNotificationLog.objects.create(recipient=recipient)
            new_recipients.append(recipient)
    notification.send(new_recipients, *args)


#
# Signals
#

if not settings.DISABLE_NOTIFICATIONS:
    @receiver(post_save, sender=Document)
    def send_document_notifications(sender, instance=None, **kwargs):
        if instance is None:
            return
        document = instance
        if document.author is None:
            return

        if not document.is_public():
            return
        subs = Subscription.objects.filter(author=document.author)
        for org in document.author.organization_set.all():
            subs |= Subscription.objects.filter(organization=org)
        for tag in document.tags.all():
            subs |= Subscription.objects.filter(tag=tag)
        recipients = []
        if document.in_reply_to_id:
            campaign = None
            try:
                campaign = document.in_reply_to.campaign
            except Campaign.DoesNotExist:
                pass
            if campaign:
                subs |= Subscription.objects.filter(campaign=campaign)
        if document.affiliation:
            subs |= Subscription.objects.filter(affiliation=document.affiliation)
        for sub in subs:
            if NotificationBlacklist.objects.filter(
                    email=sub.subscriber.email).exists():
                continue
            if document.adult and not sub.subscriber.profile.show_adult_content:
                continue
            log, created = DocumentNotificationLog.objects.get_or_create(
                recipient=sub.subscriber, document=document
            )
            if created:
                recipients.append(sub.subscriber)
        if recipients:
            send_notices(recipients, "new_post", {'document': document})

    @receiver(post_save, sender=Comment)
    def send_comment_notifications(sender, instance=None, **kwargs):
        # Only fire on creation.
        if instance is None or 'created' not in kwargs:
            return
        comment = instance
        if comment.document is None:
            return

        # Create default subscription for commenter.
        sub, created = Subscription.objects.get_or_create(
                subscriber=comment.user,
                document=comment.document
        )

        # Send notices to all subscribed parties.
        subs = Subscription.objects.filter(document=comment.document)
        recipients = []
        for sub in subs:
            if NotificationBlacklist.objects.filter(
                    email=sub.subscriber.email).exists():
                continue
            # No notification if the subscriber is the comment author. :)
            if sub.subscriber == comment.user:
                continue
            log, created = CommentNotificationLog.objects.get_or_create(
                recipient=sub.subscriber, comment=comment
            )
            if created:
                recipients.append(sub.subscriber)
        if recipients:
            send_notices(recipients, "new_reply", {'comment': comment})

