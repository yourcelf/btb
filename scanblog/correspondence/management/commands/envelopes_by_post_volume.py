import os

from django.core.management.base import BaseCommand
from django.db.models import Count

from profiles.models import Profile
from correspondence.utils import build_envelope

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            out_dir = args[0]
        except IndexError:
            print "Requires arg: <output directory>"
            return

        qs = Profile.objects.enrolled().annotate(
                count=Count('user__documents_authored')
        )

        for i,profile in enumerate(qs):
            env = build_envelope(
                profile.user.organization_set.all()[0].mailing_address,
                profile.full_address()
            )
            fn = os.path.join(out_dir, "%03d-%s.jpg" % (i, profile.get_blog_slug()))
            with open(fn, 'w') as fh:
                fh.write(env.getvalue())
