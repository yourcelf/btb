from django.db import models
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver
from django.core.mail import mail_managers
from django.utils.translation import ugettext_noop as _
from django.contrib.sites.models import Site
from django.template.loader import render_to_string

from scanning.models import Document, TranscriptionRevision
from annotations.models import Note
from comments.models import Comment


if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification

    @receiver(signals.post_syncdb, sender=notification)
    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type(
            "new_reply", _("New reply"),
            _("new reply to a post you're following"),
        )
        notification.create_notice_type(
            "new_post", _("New post"),
            _("new letter from an author or subject you're following"),
        )
else:
    print "Skipping creation of NoticeTypes as notification app is not " \
          "installed"

#
# Admin emails for site events.
#

if not settings.DISABLE_ADMIN_NOTIFICATIONS:
    @receiver(signals.post_save, sender=Document)
    def profile_notification(sender, instance, *args, **kwargs):
        if instance.author.groups.filter(name='moderators').exists():
            return
        if instance.author.profile.in_prison == False:
            mail_managers("Visitor profile document added", render_to_string(
                "btb/admin-visitor-profile-notification.txt", {
                    'document': instance,
                    'site': Site.objects.get_current(),
                }))

    @receiver(signals.post_save, sender=TranscriptionRevision)
    def transcription_notification(sender, instance, *args, **kwargs):
        if instance.editor.groups.filter(name='moderators').exists():
            return
        mail_managers("Transcription edited", render_to_string(
            "btb/admin-email-transcription-edited.txt", {
                'document': instance.transcription.document,
                'transcription': instance.transcription,
                'revision': instance,
                'site': Site.objects.get_current(),
            }))

    @receiver(signals.post_save, sender=Comment)
    def comment_notification(sender, instance, *args, **kwargs):
        if instance.user.groups.filter(name='moderators').exists():
            return
        subject = "New comment" if 'created' in kwargs else "Comment edited"
        mail_managers(subject, render_to_string(
            "btb/admin-email-comment-posted.txt", {
                'comment': instance,
                'site': Site.objects.get_current(),
            }))

    @receiver(signals.post_save, sender=Note)
    def flag_notification(sender, instance, *args, **kwargs):
        if 'created' in kwargs and instance.important and "FLAG" in instance.text:
            if instance.creator.groups.filter(name='moderators').exists():
                return
            mail_managers("Content flagged", render_to_string(
                "btb/admin-content-flagged.txt", {
                    'note': instance,
                    'site': Site.objects.get_current(),
                }))
