import os
import json
import codecs
import random
import datetime
from django.conf import settings
from django.core.management import BaseCommand
from django.core.mail import mail_managers
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.template import loader, Context

from comments.models import Comment
from profiles.models import Organization
from scanning.models import Document, Scan, PendingScan
from correspondence.models import Letter
from correspondence.views import needed_letters
from annotations.models import Note


def send_org_mail(org):
    ctx = {'site': Site.objects.get_current(), 'org': org}
    # Get a random org moderator for permissioning.
    now = datetime.datetime.now()

    try:
        org_user = org.moderators.all()[0]
    except IndexError:
        print "No moderators found for {0}; skipping.".format(org.name)
        return

    # Pending scans.
    ps =  PendingScan.objects.org_filter(org_user).filter(
                completed__isnull=True
            ).order_by('created')
    finished_ps = PendingScan.objects.org_filter(org_user).filter(
                completed__isnull=False
            ).order_by('-completed')
    ctx['pendingscans'] = { 'count': ps.count(), }
    if ctx['pendingscans']['count'] > 0:
        ctx['pendingscans']['oldest'] = ps[0]
        overdue = ctx['pendingscans']['oldest'].created < \
            (now - datetime.timedelta(days=7))
        ctx['pendingscans']['overdue'] = overdue
    try:
        ctx['pendingscans']['last_completed'] = finished_ps[0]
    except IndexError:
        pass

    # Scans.
    scans = Scan.objects.org_filter(org_user).filter(
            processing_complete=False
        ).order_by('created')
    finished_scans =  Scan.objects.org_filter(org_user).filter(
            processing_complete=True
        ).order_by('-modified')
    ctx['scans'] = {'count': scans.count()}
    if ctx['scans']['count'] > 0:
        ctx['scans']['oldest'] = scans.order_by('created')[0]
        ctx['scans']['overdue'] = ctx['scans']['oldest'].created < \
                (now - datetime.timedelta(days=7))
    try:
        ctx['scans']['last_completed'] = finished_scans[0]
    except IndexError:
        pass

    # Documents.
    all_docs = Document.objects.org_filter(org_user).exclude(
            author__profile__managed=False,
        ).exclude(
            scan__isnull=True
        )
    docs = all_docs.filter(status="unknown").order_by('scan__created')
    finished_docs =  all_docs.filter(status="unknown").order_by('-modified')
    
    ctx['documents'] = { 'count': docs.count() }
    if ctx['documents']['count'] > 0:
        ctx['documents']['oldest'] = docs.order_by('scan__created')[0]
        overdue = ctx['documents']['oldest'].scan.created < \
                (now - datetime.timedelta(days=14))
        ctx['documents']['overdue'] = overdue
    try:
        ctx['documents']['last_completed'] = finished_docs[0]
    except IndexError:
        pass

    # Outgoing mail
    needed = needed_letters(org_user).items()
    ctx['outgoing_mail'] = {}
    for letter_type, recipients in needed:
        all_letters = Letter.objects.mail_filter(org_user).filter(
                type=letter_type
        )
        try:
            latest = Letter.objects.mail_filter(org_user).filter(
                    sent__isnull=False
            ).order_by('-sent')[0]
        except IndexError:
            latest = None
        ctx['outgoing_mail'][letter_type] = {
            'count': recipients.count(),
            'last_completed': latest,
        }
        if ctx['outgoing_mail'][letter_type]['count'] > 0:
            if letter_type in ('waitlist', 'consent_form'):
                due_since = recipients.order_by('user__date_joined')[0].user.date_joined
            elif letter_type == 'enqueued':
              due_since = recipients.order_by('created')[0].created
            elif letter_type == 'comments':
              due_since = Comment.objects.unmailed().order_by('created')[0].created
            elif letter_type == 'signup_complete':
                try:
                    due_since = Document.objects.filter(
                            type='license',
                    ).exclude(
                        author__received_letters__type="signup_complete"
                    ).order_by('created')[0].created
                except IndexError:
                    due_since = None
            elif letter_type == 'first_post':
                try:
                    due_since = Document.objects.public().filter(
                        Q(type='post') | Q(type='profile')
                    ).exclude(
                        author__received_letters__type="first_post"
                    ).order_by('created')[0].created
                except IndexError:
                    due_since = None
            else:
                due_since = None
            if due_since:
                ctx['outgoing_mail'][letter_type]['due_since'] = due_since
                if letter_type != 'consent_form':
                    ctx['outgoing_mail'][letter_type]['overdue'] = due_since < (
                        now - datetime.timedelta(days=7)
                    )

    # Tickets
    tickets = Note.objects.org_filter(org_user).filter(
            resolved__isnull=True
    )
    finished_tickets =  Note.objects.org_filter(org_user).filter(
            resolved__isnull=False
        ).order_by('-resolved')
    ctx['tickets'] = { 'count': tickets.count() }
    if ctx['tickets']['count'] > 0:
        ctx['tickets']['important'] = tickets.filter(important=True).count()
        ctx['tickets']['oldest'] = tickets.order_by('created')[0]
        overdue = ctx['tickets']['oldest'].created < \
                (now - datetime.timedelta(days=14))
        ctx['tickets']['overdue'] = overdue
    try:
        ctx['tickets']['last_completed'] = finished_tickets[0]
    except IndexError:
        pass
    

    ctx['inbox_zero_distance'] = 0
    for kind in ('scans', 'documents', 'tickets', 'pendingscans'):
        ctx['inbox_zero_distance'] += ctx[kind]['count']
    for letter_type, details in ctx['outgoing_mail'].iteritems():
        if letter_type != 'consent_form':
            ctx['inbox_zero_distance'] += details['count']

    # Flavor
    with open(os.path.join(
                os.path.dirname(__file__),
                "collective_nouns.json"
            )) as fh:
        collective_nouns = json.load(fh).items()
        noun = random.choice(collective_nouns)
        ctx['collective_noun'] = {
            'thing': noun[0],
            'names_and_conditions': noun[1],
        }
    
    t = loader.get_template("btb/org_status_email.html")
    html = t.render(Context(ctx))

    mail_managers(
        subject="Distance from inbox-zero: {0}".format(
            ctx['inbox_zero_distance']
        ),
        message="",
        html_message=html,
    )

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        """
        A status email sent to an org which aims to answer the general
        questions of "what work needs to be done?" and "what work has recently
        been done?".  More specifically:
         - How much logged incoming mail hasn't been processed, and how old is
           it?
         - How many scans need to be processed, and how old are they?
         - How many documents have been split, but still need attention, and
           how old are they?
         - How much outgoing mail is enqueued for each type, and when was the
           last time each of those types were sent?
        """

        if settings.DISABLE_ADMIN_NOTIFICATIONS:
            print "Admin notifications are disabled; sending nothing."


        for org in Organization.objects.all():
            send_org_mail(org)

