import os

from django.core.management.base import BaseCommand

from profiles.models import Profile
from correspondence.utils import Postcard

class Command(BaseCommand):
    def handle(self, *args):
        try:
            (width, height, kind, outputdir) = args
        except IndexError:
            print "Requires args: x, y, group, outdir"
            return

        for profile in getattr(Profile.objects, kind):
            postcard = Postcard(width, height)
            postcard.draw_address(profile.full_address())
            postcard.save(os.path.join(outputdir, profile.get_blog_slug() + ".png"))
