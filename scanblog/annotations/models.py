import string
import random
import datetime

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist

from btb.utils import date_to_string, OrgQuerySet, OrgManager

class NoteManager(OrgManager):
    def open_tickets(self):
        return self.filter(resolved__isnull=True)

    def closed_tickets(self):
        return self.filter(resolved__isnull=False)

class Note(models.Model):
    resolved = models.DateTimeField(blank=True, null=True)
    important = models.BooleanField()
    text = models.TextField()

    creator = models.ForeignKey(User, related_name='notes_authored')
    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(default=datetime.datetime.now)

    # Foreign keys to any type that might have notes.  To add a type, migrate
    # with a new column.  Much better than generic relations, which are 
    # like totally ARGH.
    scan = models.ForeignKey('scanning.Scan', blank=True, null=True, 
            related_name='notes')
    document = models.ForeignKey('scanning.Document', blank=True, null=True, 
            related_name='notes')
    user = models.ForeignKey('auth.User', blank=True, null=True, 
            related_name='notes')
    comment = models.ForeignKey('comments.Comment', blank=True, null=True,
            related_name='notes')

    objects = NoteManager()

    class QuerySet(OrgQuerySet):
        orgs = [
            "scan__author__organization", 
            "document__author__organization", 
            "user__organization",
            "comment__document__author__organization",
        ]

        def by_resolution(self):
            return self.extra(
                select={'is_resolved': 'annotations_note.resolved is NULL'},
                order_by=['-is_resolved', '-important', '-created']
            )

    def content_object(self):
        if self.user:
            obj = self.user.profile 
        elif self.scan:
            obj = self.scan
        elif self.document:
            obj = self.document
        elif self.comment:
            obj = self.comment
        else:
            raise Exception("Unknown object for note %s" % self.pk)
        return obj

    def to_dict(self):
        obj = self.content_object()
        props = {
                'id': self.pk,
                'user_id': self.user_id,
                'scan_id': self.scan_id,
                'document_id': self.document_id,
                'resolved': date_to_string(self.resolved),
                'important': self.important,
                'text': self.text,
                'object': obj.to_dict(),
                'object_type': obj._meta.object_name.lower(),
                'creator': self.creator.profile.to_dict(),
                'modified': date_to_string(self.modified),
                'created': date_to_string(self.created),
        }
        return props

    def get_object_url(self):
        return self.content_object().get_absolute_url()

    def is_resolved(self):
        return bool(self.resolved)

    def __unicode__(self):
        return "{0} {1} {2}: {3}".format(
             self.pk,
            "CLOSED" if self.resolved else "OPEN",
            self.content_object()._meta.object_name.lower(),
            self.text[0:50] + "...",
        )

    class Meta:
        ordering = ['-important', '-created']

class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True, db_index=True)

    post_count = models.IntegerField(default=0, 
        help_text="Denormalized count of posts with this tag.")

    def __unicode__(self):
        return self.name

class ReplyCode(models.Model):
    # Avoiding ambiguous characters like s5z2l1o0...
    CHARACTERS = "abcdefghijkmnpqrtuvwxy2346789"
    code = models.CharField(max_length=16, 
            db_index=True, blank=True, unique=True)

    objects = OrgManager()

    class QuerySet(OrgQuerySet):
        orgs = ["document__author__organization"]


    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                self.code = self._random_string()
                if not ReplyCode.objects.filter(code=self.code).exists():
                    break
        super(ReplyCode, self).save(*args, **kwargs)

    def _random_string(self, length=4):
        return ''.join(random.choice(self.CHARACTERS) for i in range(length))
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
        }

    def doc_dict(self):
        try:
            document = self.document
        except ObjectDoesNotExist:
            document = None
        finally:
            if document:
                dd = {
                    'id': document.pk,
                    'title': unicode(document.get_title()),
                    'author': document.author.profile.to_dict(),
                    'type': document.type,
                    'date_written': document.date_written.isoformat(),
                    'url': document.get_absolute_url(),
                    'edit_url': document.get_edit_url(),
                    'comment_count': document.comments.count(),
                }
            else:
                dd = None
        return {
            'id': self.pk,
            'code': self.code,
            'document': dd,
        }

    def __unicode__(self):
        return self.code
