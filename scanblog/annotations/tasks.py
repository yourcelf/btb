from celery.task import task
from django.core.mail import mail_managers, mail_admins
from django.contrib.sites.models import Site
from django.template.loader import render_to_string

from annotations.models import Note

@task
def send_flag_notification_email(note_id):
    try:
        note = Note.objects.select_related('user').get(pk=note_id)
    except Note.DoesNotExist:
        return
    if not note.creator.is_active:
        return
    mail_admins("Content flagged", render_to_string(
        "btb/admin-content-flagged.txt", {
            'note': note,
            'site': Site.objects.get_current()
        }))
