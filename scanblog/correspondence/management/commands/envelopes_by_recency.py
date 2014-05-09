import os

from django.core.management.base import BaseCommand
from django.db.models import Count

from profiles.models import Profile
from correspondence.utils import build_envelope, write_csv

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            out_dir = args[0]
        except IndexError:
            print "Requires arg: <output directory>"
            return

        data = []

        qs = Profile.objects.enrolled().select_related('user')
        for profile in qs:
            docs = profile.user.documents_authored.filter(status='published')
            try:
                latest = docs.order_by('-date_written')[0]
            except IndexError:
                continue
            data.append((
                latest.date_written.strftime("%y-%m-%d"),
                profile
            ))
        data.sort()
        data.reverse()
        rows = []
        for i,(date,profile) in enumerate(data[:250]):
            rows.append([
                str(i),
                str(profile.pk),
                profile.display_name
            ])

            env = build_envelope(
                profile.user.organization_set.all()[0].mailing_address,
                profile.full_address()
            )
            fn = os.path.join(out_dir, "%03d-%s.jpg" % (i, profile.get_blog_slug()))
            with open(fn, 'w') as fh:
                fh.write(env.getvalue())
        write_csv(rows, os.path.join(out_dir, "manifest.csv"))
        

