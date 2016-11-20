import os
import json
import shutil
import random
import datetime

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

from sorl.thumbnail import delete as thumbnail_delete
from sorl.thumbnail.helpers import ThumbnailError
from annotations.models import ReplyCode
from comments.models import Comment
from btb.utils import OrgManager, OrgQuerySet
from scanning.templatetags.public_url import public_url

TMP_UPLOAD = os.path.join(settings.UPLOAD_TO, "tmp")

def public_path(private_path):
    return os.path.join(
        settings.PUBLIC_MEDIA_ROOT,
        os.path.relpath(private_path, settings.MEDIA_ROOT))

#
# Models and managers
#

class PendingScanManager(OrgManager):
    def pending(self):
        return self.filter(scan__isnull=True, completed__isnull=True)

    def missing(self):
        return self.filter(scan__isnull=True, completed__isnull=False)

    def fulfilled(self):
        return self.filter(scan__isnull=False)

class PendingScan(models.Model):
     # Trying to avoid ambiguous letters (when written by hand)
    CHARACTERS = "abcdefghijkmnpqrtuvwxy2346789"

    editor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="pending_scans_edited")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="pending_scans_authored")
    org = models.ForeignKey('profiles.Organization', null=True)

    scan = models.OneToOneField('Scan', blank=True, null=True)
    code = models.CharField(max_length=12)
    completed = models.DateTimeField(blank=True, null=True)

    created = models.DateTimeField(default=datetime.datetime.now)
    modified = models.DateTimeField(auto_now=True)

    objects = PendingScanManager()

    class QuerySet(OrgQuerySet):
        orgs = ["scan__author__organization", "org"]

    def _random_string(self, length=4):
        return ''.join(random.choice(self.CHARACTERS) for i in range(length))

    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                self.code = self._random_string()
                if not PendingScan.objects.filter(code=self.code).exists():
                    break
        super(PendingScan, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            'id': self.pk,
            'editor': self.editor.profile.to_dict(),
            'author': self.author.profile.to_dict(),
            'scan_id': self.scan_id,
            'code': self.code,
            'completed': self.completed.isoformat() if self.completed else None,
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
        }

    def __unicode__(self):
        return u"{0}: {1}".format(self.editor.profile.display_name, 
                                  self.created)

    class Meta:
        ordering = ['-created']


class Scan(models.Model):
    """
    This is the raw scan with envelope and all.
    """
    pdf = models.FileField(upload_to=TMP_UPLOAD, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="scans_authored", 
            blank=True, null=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="scans_uploaded")
    org = models.ForeignKey('profiles.Organization', null=True)

    processing_complete = models.BooleanField(default=False)
    under_construction = models.BooleanField(default=False)

    created = models.DateTimeField(default=datetime.datetime.now)
    modified = models.DateTimeField(default=datetime.datetime.now)

    # A unique ID identifying this scan by an external source (e.g. mail
    # scanner) which we can use to track whether a document has been loaded or
    # not.
    source_id = models.CharField(blank=True, max_length=100)

    objects = OrgManager()

    class QuerySet(OrgQuerySet):
        orgs = ["author__organization", "org"]

    def save(self, *args, **kwargs):
        self.modified = datetime.datetime.now()
        super(Scan, self).save(*args, **kwargs)

    def to_dict(self):
        try:
            lock = self.editlock_set.all()[0].to_dict()
        except IndexError:
            lock = None
        try:
            code = self.pendingscan.code
        except PendingScan.DoesNotExist:
            code = None
        return {
            'id': self.pk,
            'pdf': self.pdf.url,
            'author': self.author.profile.to_dict() if self.author else None,
            'uploader': self.uploader.profile.to_dict(),
            'processing_complete': self.processing_complete,
            'under_construction': self.under_construction,
            'created': self.created.isoformat() if self.created else None,
            'modified': self.modified.isoformat() if self.modified else None,
            'pages': [p.to_dict() for p in self.scanpage_set.all()],
            'url': self.get_absolute_url(),
            'edit_url': self.get_edit_url(),
            'lock': lock,
            'pendingscan_code': code,
        }

    def get_absolute_url(self):
        return reverse("moderation.home") + "#/process/scan/{0}".format(self.pk)

    def get_edit_url(self):
        return self.get_absolute_url()

    def full_delete(self, filesonly=False):
        for doc in self.document_set.all():
            doc.full_delete(filesonly)
        for page in self.scanpage_set.all():
            page.full_delete(filesonly)
        if self.pdf:
            self.pdf.delete()
        if not filesonly:
            self.delete()
            
    class Meta:
        ordering = ['created']
        permissions = (
                ('view_raw_scans', 'View raw scans'),
        )
	
    def __unicode__(self):
        return "(%s) %s" % (self.pk or "", self.pdf.name)

class ScanPage(models.Model):
    """
    Represents one page of a raw scan and its order in the entire scan.
    """
    scan = models.ForeignKey(Scan)
    order = models.IntegerField(default=0)
    image = models.ImageField(upload_to=TMP_UPLOAD)

    def to_dict(self):
        return {
            'id': self.pk,
            'scan_id': self.scan_id,
            'order': self.order,
            'image': self.image.url,
            'image_dims': [self.image.width, self.image.height],
        }

    def full_delete(self, filesonly=False):
        self.remove_thumbnails()
        if self.image and os.path.exists(self.image.path):
            self.image.delete()
        if not filesonly:
            self.delete()

    def remove_thumbnails(self):
        try:
            thumbnail_delete(self.image.path, delete_file=False)
        except ThumbnailError:
            pass

    def page_number(self):
        return self.order + 1

    class Meta:
        unique_together = (('order', 'scan'))
        ordering = ['order']

class DocumentManager(OrgManager):
    def public(self):
        """
        Note that "public" here implies public and in prison.
        """
        return self.all().select_related(
                    'author', 'author__profile', 'transcription'
                ).filter(
                    status="published",
                    author__is_active=True,
                    author__profile__consent_form_received=True,
                )

    def safe(self):
        return self.public().filter(adult=False)

    def safe_for_user(self, user):
        if user.is_authenticated() and user.profile.show_adult_content:
            return self.public()
        else:
            return self.safe()

    def ready(self):
        return self.filter(
                status="ready", 
                author__is_active=True, 
                author__profile__consent_form_received=True
            ).order_by('created')

class Document(models.Model):
    """
    This is a parsed section of a scan.
    """
    DOCUMENT_TYPES = (
        ('license','license'),
        ('photo', 'photo'),
        ('post','post'),
        ('profile','profile'),
        ('request','request'),
    )
    STATES = (
        ("unknown", "Needs attention"),
        ("ready", "Ready to publish"),
        ("published", "Published"),
        ("unpublishable", "Can't be published"),
    )

    scan = models.ForeignKey(Scan, null=True, blank=True) # Null for text-only posts
    pdf = models.FileField(upload_to=TMP_UPLOAD, blank=True)
    body = models.TextField(blank=True)

    # Metadata
    type = models.CharField(max_length=25, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=255, blank=True)
    affiliation = models.ForeignKey('profiles.Affiliation',
            blank=True, null=True)
    in_reply_to = models.ForeignKey('annotations.ReplyCode', 
        related_name="document_replies", blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='documents_authored')
    date_written = models.DateTimeField(null=True)
    highlight = models.ImageField(upload_to=TMP_UPLOAD, blank=True)
    highlight_transform = models.TextField(blank=True)

    # Locking
    under_construction = models.BooleanField(
        default=False,
        help_text="Deprecated, don't use.  Use status instead.")

    # State
    status = models.CharField(max_length=20, choices=STATES, 
                              db_index=True, default="unknown")
    adult = models.BooleanField(default=False)
    comments_disabled = models.BooleanField(default=False)

    tags = models.ManyToManyField('annotations.Tag', blank=True)
    reply_code = models.OneToOneField('annotations.ReplyCode')

    editor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='documents_edited',
            help_text="The last person to edit this document.")
    created = models.DateTimeField(default=datetime.datetime.now)
    modified = models.DateTimeField(default=datetime.datetime.now)

    objects = DocumentManager()

    class QuerySet(OrgQuerySet):
        orgs = ["author__organization"]

    def save(self, *args, **kwargs):
        if not self.date_written:
            self.date_written = datetime.datetime.now()
        if not self.reply_code_id:
            self.reply_code = ReplyCode.objects.create()
        self.modified = datetime.datetime.now()
        super(Document, self).save(*args, **kwargs)
        self.set_publicness()
        self.update_comment()

    def update_comment(self):
        """
        Creates the shadow comment object to hold this document's place in a
        commment thread, if this document is a reply to comments.
        """
        # Create comment objects only when the doc is public.  That way,
        # subscription signals are fired at the right moment -- the comment is
        # public and viewable.
        parent = None
        if self.in_reply_to:
            try:
                parent = self.in_reply_to.document
            except Document.DoesNotExist:
                pass
        if parent and self.is_public():
            # Only create a comment object if we are public.
            try:
                comment = self.comment
            except Comment.DoesNotExist:
                comment = Comment()
            comment.user = self.author
            comment.removed = False
            comment.document = parent
            comment.comment_doc = self
            comment.save()
        else:
            # If we've gone non-public, mark the comment removed rather
            # than deleting.  That way, we don't re-fire subscriptions if
            # the doc is only temporarily un-published.
            try:
                self.comment.removed = True
                self.comment.save()
            except Comment.DoesNotExist:
                pass

    def is_public(self):
        """
        Note: this logic is duplicated in the Document class for individual
        documents querying their own publicness.
        """
        return self.status == "published" and self.author.profile.is_public()

    def set_publicness(self):
        if self.is_public():
            self.make_files_public()
        else:
            self.make_files_private()

    def file_dir(self):
        if self.pdf:
            return os.path.dirname(self.pdf.path)
        elif self.scan:
            return "{0}doc{1}".format(
                os.path.splitext(self.scan.pdf.path)[0],
                self.pk
            )
        else:
            return None

    def get_basename(self):
        """
        Make sure each document gets its own folder.  Public/private for files
        is controlled by symlinks pointing to the document folders.
        """
        fd = self.file_dir()
        if fd:
            return "{0}/doc{1}".format(
                fd,
                self.pk
            )
        return None

    def make_files_public(self):
        file_dir = self.file_dir()
        if file_dir:
            link_path = public_path(file_dir)
            if not os.path.lexists(link_path):
                parent = os.path.dirname(link_path)
                if not os.path.exists(parent):
                    os.makedirs(parent)
                os.symlink(file_dir, link_path)

    def make_files_private(self):
        file_dir = self.file_dir()
        if file_dir:
            link_path = public_path(file_dir)
            if os.path.lexists(link_path):
                os.remove(link_path)
            # For cleanliness, try deleting parent directory.
            try:
                # Throws OSError harmlessly if parent directory is not empty.
                os.rmdir(os.path.dirname(link_path))
            except OSError:
                pass
            self.remove_thumbnails()

    def remove_thumbnails(self):
        try:
            thumbnail_delete(self.highlight, delete_file=False)
        except ThumbnailError:
            pass
        for page in self.documentpage_set.all():
            try:
                thumbnail_delete(page.image.path, delete_file=False)
            except ThumbnailError:
                pass

    def _get_post_url(self):
        return reverse("blogs.post_show", args=[self.pk, self.get_slug()])

    def get_standalone_url(self):
        if self.type == "post":
            return self._get_post_url()
        else:
            return self.get_absolute_url()

    def get_absolute_url(self):
        if self.type == "post":
            # Be careful to avoid accidental recursion here, if a document ever
            # gets listed as in-reply-to itself.
            url = None
            try:
                if self.comment.document != self and self.comment.removed == False:
                    return self.comment.get_absolute_url()
            except Comment.DoesNotExist:
                pass
            return self._get_post_url()
        elif self.type == "profile":
            return reverse("profiles.profile_show", args=[self.author.pk])
        else:
            return self.get_edit_url()

    def mark_favorite_url(self):
        return "%s?document_id=%s" % (reverse("comments.mark_favorite"), self.pk)

    def mark_favorite_after_login_url(self):
        return "%s?document_id=%s" % (reverse("comments.mark_favorite_after_login"), self.pk)

    def unmark_favorite_url(self):
        return "%s?document_id=%s" % (reverse("comments.unmark_favorite"), self.pk)

    def list_favorites_url(self):
        return "%s?document_id=%s" % (reverse("comments.list_favorites"), self.pk)

    def get_edit_url(self):
        return "%s#/process/document/%s" % (reverse("moderation.home"), self.pk)

    def human_status(self):
        for s,h in self.STATES:
            if s == self.status:
                return h

    def to_dict(self):
        return {
            'id': self.pk,
            'scan_id': self.scan_id,
            'type': self.type,
            'title': self.title,
            'affiliation': self.affiliation.to_dict() if self.affiliation else None,
            'body': self.body,
            'adult': self.adult,
            'in_reply_to': self.in_reply_to.code if self.in_reply_to else None,
            'reply_code': self.reply_code.code,
            'author': self.author.profile.to_dict(),
            'date_written': self.date_written.isoformat() if self.date_written else None,
            'highlight': self.highlight.url if self.highlight else None,
            'highlight_transform': json.loads(self.highlight_transform) if self.highlight_transform else "",
            'status': self.status,
            'pdf': self.pdf.url if self.pdf else None,
            'public_pdf': public_url(self.pdf.url) if self.pdf else None,
            'editor': self.editor.profile.to_dict(),
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
            'pages': [p.to_dict() for p in self.documentpage_set.all()],
            'tags': ";".join([t.name for t in self.tags.all()]),
            'url': self.get_absolute_url(),
            'edit_url': self.get_edit_url(),
            'comment_count': self.comments.count(),
            'notes_count': self.notes.count(),
            'is_public': self.is_public(),
        }

    def full_delete(self, filesonly=False):
        self.remove_thumbnails()
        if self.pdf:
            self.pdf.delete(False)
        if self.highlight:
            self.highlight.delete(False)
        for page in self.documentpage_set.all():
            page.full_delete(filesonly)
        if not filesonly:
            self.make_files_private()
            try:
                if self.file_dir():
                    os.rmdir(self.file_dir())
            except OSError:
                pass
            self.delete()
        else:
            self.save()


    def __unicode__(self):
        if self.type == "post":
            return unicode(self.get_title())
        elif self.type == "profile":
            return unicode(self.author.profile)
        else:
            return unicode(self.pk)

    def get_title(self):
        return (self.title or _("Untitled")).strip()

    def get_slug(self):
        return slugify(self.title)

    class Meta:
        ordering = ['-date_written']
        permissions = (("tag_post", "Tag posts"),)

class DocumentPage(models.Model):
    """
    Represents one page of a processed document and its order in the entire
    document.
    """
    document = models.ForeignKey(Document)
    scan_page = models.ForeignKey(ScanPage)
    order = models.IntegerField()
    image = models.ImageField(upload_to=TMP_UPLOAD, max_length=255, 
                              blank=True, null=True)
    transformations = models.TextField(help_text="Serialized description of transformations that change the original scan_page image to the image for this document.", blank=True)

    def save(self, *args, **kwargs):
        if not self.image:
            image = self.get_image_path()
            if not os.path.exists(os.path.dirname(image)):
                os.makedirs(os.path.dirname(image))
            if not os.path.exists(image):
                shutil.copy(self.scan_page.image.path, image)
            self.image = os.path.relpath(image, settings.MEDIA_ROOT)
        super(DocumentPage, self).save(*args, **kwargs)
    
    def to_dict(self):
        return {
            'id': self.pk,
            'document_id': self.document_id,
            'scan_page': self.scan_page.to_dict(),
            'order': self.order,
            'image': self.image.url if self.image else None,
            'public_image': public_url(self.image.url) if self.image else None,
            'transformations': json.loads(self.transformations) if self.transformations else "",
        }

    def full_delete(self, filesonly=False):
        if self.image and os.path.exists(self.image.path):
            os.remove(self.image.path)
        if not filesonly:
            self.delete()

    def get_image_path(self):
        return "%s-page-%s.jpg" % (self.document.get_basename(), self.order)

    def page_number(self):
        return self.order + 1

    class Meta:
        unique_together = (('order', 'document'))
        ordering = ['order']

class Transcription(models.Model):
    """
    This is the transcription of an entire document.
    """
    document = models.OneToOneField('Document')
    complete = models.BooleanField(
            default=False,
            help_text=_("Check if transcription is complete"))
    locked = models.BooleanField(default=False)
    created = models.DateTimeField(default=datetime.datetime.now)

    def current(self):
        try:
            return self.revisions.all()[0]
        except IndexError:
            return None

    class Meta:
        permissions = (
            ('lock_transcription', 'Lock transcription'),
            ('change_locked_transcription', 'Change locked transcriptions'),
        )


class TranscriptionRevision(models.Model):
    """
    This is a revision of the transcription of an entire document.
    """
    transcription = models.ForeignKey(Transcription, related_name="revisions")
    revision = models.IntegerField(default=0)
    body = models.TextField()
    editor = models.ForeignKey(settings.AUTH_USER_MODEL)
    modified = models.DateTimeField(default=datetime.datetime.now)
	
    class Meta:
        ordering = ['-revision']
        unique_together = [('transcription', 'revision')]

class EditLock(models.Model):
    scan = models.ForeignKey(Scan, null=True, blank=True)
    document = models.ForeignKey(Document, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    created = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'scan_id': self.scan_id,
            'docment_id': self.document_id,
            'user': self.user.profile.to_dict(),
            'created': self.created.isoformat(),
            'now': datetime.datetime.now().isoformat(),
        }

    def __unicode__(self):
        if self.document_id:
            stub = "Doc %s" % self.document_id
        elif self.scan_id:
            stub = "Scan %s" % self.scan_id
        else:
            stub = "Invalid"
        return " ".join((stub, self.user.username, self.created.isoformat()))

