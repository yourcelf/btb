import re
import sys
import csv
import StringIO

from django.core.management import BaseCommand

from profiles.models import Profile
from comments.models import Comment

class Command(BaseCommand):
    help = "Extract a CSV showing user_id, status, post volume, comment volume, reply volume, zip code"

    zip_re = re.compile("(\d{5})(?:[-\s\d\.]*)$")

    def handle(self, *args, **kwargs):
        # Answer the following questions:
        # 1. What are the zip codes for the addresses of all active writers?
        rows = []
        sio = StringIO.StringIO()
        writer = csv.writer(sio)
        for p in Profile.objects.bloggers():
            if p.consent_form_received:
                status = "enrolled"
            else:
                status = "waitlisted"
            post_count = p.user.documents_authored.filter(status="published").count()
            comment_count = Comment.objects.filter(document__author=p.user).count()
            reply_count = Comment.objects.filter(comment_doc__author=p.user).count()

            row = [p.user_id, status, post_count, comment_count, reply_count]

            match = self.zip_re.search(p.mailing_address)
            if not (match and match.group(1)):
                sys.stderr.write("Zip not found: %s\n" % repr(p.mailing_address))
                sys.stderr.write("Participation: %s\n" % repr(row))
            else:
                row.append(match.group(1))
            writer.writerow(row)
        print sio.getvalue()

