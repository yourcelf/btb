import datetime
from django.db.models import Q
from django.core.management import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.template import loader, Context
from django.core.mail import mail_managers
from django.conf import settings

from scanning.models import Transcription
from comments.models import Comment

class Command(BaseCommand):
    help = "Send a status report email to admins."

    def handle(self, *args, **kwargs):
        # Answer the following questions:
        # 1. What transcriptions/comments have been left in the last 24 hours?
        # 2. How many scans are on the dashboard, and how old?
        # 3. How many tickets are on the dashboard, and how old?
        # 4. How much mail needs to go out, and when was it last sent?
        # 5. When were the last new invitations sent?
        if settings.DISABLE_ADMIN_NOTIFICATIONS:
            print "Admin notifications are disabled; sending nothing."
            return

        then = datetime.datetime.now() - datetime.timedelta(days=1)

        ctx = {
                'site': Site.objects.get_current()
        }
        # Transcriptions
        mods = Group.objects.get(name='moderators')
        transcriptions = list(Transcription.objects.filter(
                Q(revisions__modified__gte=then),
                ~Q(revisions__editor__groups=mods)
            ).order_by('-revisions__modified').distinct())
        txrevs = []
        for tx in transcriptions:
            revs = list(tx.revisions.all()[0:4])
            pairs = []
            for i in range(len(revs)):
                if i + 1 < len(revs):
                    pair = (revs[i + 1], revs[i])
                else:
                    pair = (None, revs[i])
                pairs.append(pair)
            pairs.reverse()
            txrevs.append(pairs)
        ctx['transcriptions'] = zip(transcriptions, txrevs)

        # Comments
        ctx['comments'] = list(Comment.objects.filter(
            modified__gte=then,
        ).exclude(
            user__groups=mods
        ).exclude(
            user__profile__managed=True
        ))
            

        t = loader.get_template("btb/daily_spam_check_email.html")
        html = t.render(Context(ctx))

        if len(ctx['comments']) > 0 or len(ctx['transcriptions']) > 0:
            mail_managers(
                subject="Spam check: {0} comments, {1} transcriptions".format(
                    len(ctx['comments']), len(ctx['transcriptions'])
                ),
                message="",
                html_message=html
            )
        
        

