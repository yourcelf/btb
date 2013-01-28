import os
import datetime

from django.db import models
from django.contrib.auth.models import User

from comments.models import Comment
from scanning.models import Document
from btb.utils import date_to_string, OrgQuerySet, OrgManager

from correspondence.generate import generate_file, generate_colation

class LetterManager(OrgManager):
    def unsent(self):
        return self.filter(sent__isnull=True, recipient__profile__lost_contact=False)

    def sent(self):
        return self.filter(sent__isnull=False)

class Letter(models.Model):
    TYPES = ("letter", 
            "consent_form", 
            "signup_complete", 
            "first_post", 
            "printout",
            "comments", 
            "waitlist",
            "returned_original",
            "refused_original")
    sender = models.ForeignKey(User, related_name="authored_letters", blank=True)

    recipient = models.ForeignKey(User, blank=True, null=True, 
            related_name="received_letters")

    org = models.ForeignKey('profiles.Organization', blank=True, null=True,
            help_text="Organization for the return address for this letter")

    body = models.TextField(blank=True)
    is_postcard = models.BooleanField(default=False)
    send_anonymously = models.BooleanField(default=False)

    type = models.CharField(max_length=255, choices=[(a, a) for a in TYPES])
    auto_generated = models.BooleanField(default=False)
    document = models.ForeignKey(Document, null=True, blank=True)
    comments = models.ManyToManyField(Comment, null=True, blank=True)
    created = models.DateTimeField(default=datetime.datetime.now)
    sent = models.DateTimeField(null=True)

    # File path relative to PRIVATE_MEDIA_ROOT
    file = models.FileField(upload_to="tmp", blank=True)

    # Deprecated
    recipient_address = models.TextField(blank=True, default="", 
            help_text="Legacy for old content.  No longer used.")

    objects = LetterManager()

    class QuerySet(OrgQuerySet):
        orgs = ["recipient__organization", "org"]

    def get_file(self):
        if not self.has_file():
            self.file = generate_file(self)
            if self.file:
                self.save()
        if self.file:
            return self.file.path
        return None

    def has_file(self):
        return self.file and os.path.exists(self.file.path)

    def save(self, *args, **kwargs):
        if self.pk and self.file:
            # Check for modification.  If we've been modified, clear the file. 
            orig = Letter.objects.get(pk=self.pk)
            modified = False
            # Exclude only 'sent' and 'file' from the check.
            for field in ("sender", "recipient", "recipient_address", 
                          "body", "is_postcard", "send_anonymously", 
                          "type", "document", "created"):
                if getattr(orig, field) != getattr(self, field):
                    modified = True
                    break
            modified = modified or set(self.comments.all()) != set(orig.comments.all())
            if modified:
                os.remove(self.file.path)
                self.file = ""
        elif not self.pk:
            self.file = ""
        return super(Letter, self).save(*args, **kwargs)

    def to_dict(self):
        return {
            'id': self.pk,
            'org_id': self.org_id,
            'org': self.org.to_dict() if self.org else None,
            'sender': self.sender.profile.to_dict(),
            'recipient': self.recipient.profile.to_dict() if self.recipient else None,
            'recipient_address': self.recipient_address,
            'body': self.body,
            'is_postcard': self.is_postcard,
            'type': self.type,
            'comments': [c.to_dict() for c in self.comments.all()],
            'document': self.document.to_dict() if self.document else None,
            'created': date_to_string(self.created),
            'sent': date_to_string(self.sent),
            'send_anonymously': self.send_anonymously,
        }

    def sorted_comments(self):
        return self.comments.all().order_by('document', 'created')

    def recipient_name(self):
        if self.recipient:
            return self.recipient.profile.display_name
        return self.recipient_address.split("\n")[0].strip()

    def get_recipient_address(self):
        if self.recipient:
            return "\n".join((
                self.recipient.profile.display_name, 
                self.recipient.profile.mailing_address,
            ))
        return self.recipient_address

    class Meta:
        permissions = (
            ('manage_correspondence', 'Manage correspondence'),
        )
        ordering = ['recipient', 'created']

    def __unicode__(self):
        return "%s: %s" % (self.type, self.sent)

class MailingManager(OrgManager):
    def unfinished(self):
        return self.all().filter(date_finished__isnull=True)

    def finished(self):
        return self.all().filter(date_finished__isnull=False)

class Mailing(models.Model):
    letters = models.ManyToManyField(Letter, blank=True, null=True)
    date_finished = models.DateTimeField(blank=True, null=True)
    editor = models.ForeignKey(User)
    created = models.DateTimeField(default=datetime.datetime.now)
    modified = models.DateTimeField(auto_now=True)

    file = models.FileField(upload_to="tmp", blank=True)

    objects = MailingManager()

    class QuerySet(OrgQuerySet):
        orgs = ['letters__recipient__organization',
                'letters__org']

    def __unicode__(self):
        return "{0}{1}; {2}; {3}".format(
            "*" if self.date_finished is None else "",
            self.created.strftime("%Y-%m-%d"),
            self.editor.profile.display_name,
            self.letters.count())

    def save(self, *args, **kwargs):
        if self.pk:
            for letter in self.letters.all():
                letter.sent = self.date_finished
                letter.save()
        super(Mailing, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        for letter in self.letters.all():
            if letter.auto_generated == True:
                letter.delete()
        return super(Mailing, self).delete(*args, **kwargs)

    def to_dict(self):
        light = self.light_dict()
        light['letters'] = [l.to_dict() for l in self.letters.all()]
        return light

    def light_dict(self):
        """
        Lighter weight option when you don't need a full list of letters
        """
        return {
            'id': self.pk,
            'editor': self.editor.profile.to_dict(),
            'created': date_to_string(self.created),
            'modified': date_to_string(self.modified),
            "date_finished": date_to_string(self.date_finished),
            'letter_count': self.letters.count(),
        }

    def has_file(self):
        return self.file and os.path.exists(self.file.path)

    def get_file(self):
        if not self.has_file():
            self.file = generate_colation(self)
            self.save()
        return self.file.path

    def finished(self):
        return bool(self.date_finished)

    class Meta:
        ordering = ['-created']
