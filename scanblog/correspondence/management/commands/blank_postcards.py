import os

from django.core.management.base import BaseCommand

from profiles.models import Profile
from correspondence.utils import Postcard

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            (width, height, kind, outputdir) = args
        except IndexError:
            print "Requires args: x, y, group, outdir"
            return

        try:
            os.makedirs(outputdir)
        except OSError:
            pass

        for profile in getattr(Profile.objects, kind)():
            postcard = Postcard(float(width), float(height))
            postcard.draw_address(profile.full_address())
            postcard.save(os.path.join(outputdir, profile.get_blog_slug() + ".png"))
