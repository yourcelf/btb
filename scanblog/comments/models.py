import datetime
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from btb.utils import OrgManager, OrgQuerySet

class CommentManager(OrgManager):
    def public(self):
        return self.filter(removed=False, document__status="published")

    def public_and_tombstoned(self):
        return self.filter(
                Q(removed=False) |
                Q(~Q(commentremoval__web_message=u""),
                  removed=True, commentremoval__isnull=False)
            )

    def excluding_boilerplate(self):
        return self.public().exclude(
                comment="Thanks for writing! I finished the transcription for your post."
            ).exclude(
                comment="Thanks for writing! I worked on the transcription for your post."
            ).exclude(
                comment_doc__isnull=False
            )

    def with_mailed_annotation(self):
        return self.public_and_tombstoned().annotate(letter_sent=models.Max('letter__sent'))

    def unmailed(self):
        return self.public().filter(
            comment_doc__isnull=True,
            document__isnull=False,
            document__author__is_active=True,
            document__author__profile__managed=True,
            letter__isnull=True,
        )

class Comment(models.Model):
    user = models.ForeignKey(User)
    created = models.DateTimeField(default=datetime.datetime.now)
    modified = models.DateTimeField(default=datetime.datetime.now)

    # The comment itself
    comment = models.TextField(blank=True)
    comment_doc = models.OneToOneField('scanning.Document', 
            null=True, blank=True)
    document = models.ForeignKey('scanning.Document', blank=True, null=True,
            related_name='comments')

    # Metadata
    ip_address = models.IPAddressField(blank=True, null=True)
    removed = models.BooleanField()

    objects = CommentManager()

    def clean(self):
        # Deal with https://code.djangoproject.com/ticket/5622
        if not self.ip_address:
            self.ip_address = None

    class QuerySet(OrgQuerySet):
        orgs = ["document__author__organization"]

    def get_absolute_url(self):
        if self.document:
            return "%s#c%s" % (self.document.get_absolute_url(), self.pk)
        return ""

    def mark_favorite_url(self):
        return "%s?comment_id=%s" % (reverse("comments.mark_favorite"), self.pk)

    def unmark_favorite_url(self):
        return "%s?comment_id=%s" % (reverse("comments.unmark_favorite"), self.pk)

    def list_favorites_url(self):
        return "%s?comment_id=%s" % (reverse("comments.list_favorites"), self.pk)

    def to_dict(self):
        cd = self.comment_doc
        return {
            'id': self.pk,
            'user': self.user.profile.to_dict(),
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
            'comment': self.comment,
            'comment_doc': cd.to_dict() if cd else None,
            'removed': self.removed,
            'url': self.get_absolute_url(),
            'edit_url': self.get_absolute_url(),
        }

    class Meta:
        ordering = ['created']

    def __unicode__(self):
        if self.comment:
            blurb = self.comment[:50] + "..."
        elif self.comment_doc:
            blurb = "<doc %i>" % self.comment_doc.pk
        else:
            blurb = "None"
        return "%s: %s" % (self.user.profile.display_name, blurb)

class RemovalReason(models.Model):
    """
    This is a class describing messages left behind when a comment is removed,
    and policy for notifications.  Use it when removing comments, where you
    want a side effect like a notification to the comment author or 
    """
    name = models.CharField(max_length=255, unique=True)
    organizations = models.ManyToManyField("profiles.Organization",
            help_text="To which organizations will this removal reason be visible?")
    default_web_message = models.TextField(
        help_text="Default message to display in place of the removed comment."
                  " If blank, no web message will be left.",
        blank=True
    )
    default_comment_author_message = models.TextField(
        help_text="Default message to send to commenters, if any."
                  " If blank, commenters won't be notified.",
        blank=True
    )
    default_post_author_message = models.TextField(
        help_text="Default message to send to post authors, if any."
                  " If blank, post authors won't be notified.",
        blank=True
    )

    objects = OrgManager()

    class QuerySet(OrgQuerySet):
        orgs = ["organizations"]

    def __unicode__(self):
        return self.name

class CommentRemovalManager(OrgManager):
    def needing_letters(self):
        return self.exclude(post_author_message=u"").exclude(
                comment__letter__type="comment_removal")

class CommentRemoval(models.Model):
    comment = models.OneToOneField(Comment)
    reason = models.ForeignKey(RemovalReason, blank=True, null=True)
    web_message = models.TextField(blank=True)
    comment_author_message = models.TextField(blank=True)
    post_author_message = models.TextField(blank=True)
    date = models.DateTimeField(default=datetime.datetime.now)

    objects = CommentRemovalManager()

    class QuerySet(OrgQuerySet):
        orgs = ["comment__document__author__organization"]

    def __unicode__(self):
        return "%s: %s" % (self.comment.pk, self.date)

class CommentRemovalNotificationLog(models.Model):
    comment = models.OneToOneField(Comment)
    date = models.DateTimeField(default=datetime.datetime.now)

class FavoriteManager(OrgManager):
    pass

class Favorite(models.Model):
    user = models.ForeignKey(User)
    comment = models.ForeignKey(Comment, blank=True, null=True)
    document = models.ForeignKey('scanning.Document', blank=True, null=True)
    created = models.DateTimeField(default=datetime.datetime.now)

    objects = FavoriteManager()

    class QuerySet(OrgQuerySet):
        orgs = ["document__author__organization"]

    def get_absolute_url(self):
        return self.document.get_absolute_url()

    def to_dict(self):
        return {
                'id': self.pk,
                'user_id': self.user_id,
                'comment_id': self.comment_id,
                'document_id': self.document_id,
                'url': self.get_absolute_url(),
        }

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return "%s: %s" % (self.user.profile, self.comment_id or self.document_id)
