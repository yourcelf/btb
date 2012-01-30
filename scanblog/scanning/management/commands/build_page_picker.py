import os
import json
import tempfile
import subprocess

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q

from scanning.models import DocumentPage, public_url
from sorl.thumbnail import get_thumbnail

class Command(BaseCommand):
    args = ''
    help = "Re-save all documents.  Useful for correcting public/private permissions."

    def handle(self, *args, **kwargs):
        tmpdir = "/tmp/thumbdir"
        try:
            os.makedirs(tmpdir)
        except OSError:
            pass
        dp = DocumentPage.objects.filter(
                document__status="published",
                document__author__is_active=True,
                document__author__profile__blogger=True,
                document__author__profile__consent_form_received=True,
        ).filter(
                Q(document__type='post') | Q(document__type='profile')
        ).select_related(
                'document', 'document__author', 'document__author__profile'
        ).order_by('-document__date_written', 'document__pk', 'order')
        count = dp.count()

        thumb_size = [38, 50]
        num_thumbs = 576

        dir_name = os.path.join("public", "pagepicker")
        dir_path = os.path.join(settings.MEDIA_ROOT, dir_name)
        try:
            os.makedirs(dir_path)
        except OSError:
            pass

        manifest = []
        for i in range(0, count, num_thumbs):
            page_images = []
            page_data = []
            for page in dp[i:i + num_thumbs]:
                thumb_dest = os.path.join(tmpdir, "%s.jpg" % page.pk)
                if not os.path.exists(thumb_dest):
                    proc = subprocess.Popen(["nice", "convert",
                        "-background", "white",
                        "-resize", "{0}x{1}".format(*thumb_size),
                        page.image.path,
                        thumb_dest])
                    proc.communicate()
                page_images.append(thumb_dest)

                if page.document.type == "profile":
                    title = "Profile"
                else:
                    title = unicode(page.document.get_title())

                page_data.append({
                    'img_url': public_url(page.image.url),
                    'url': page.document.get_absolute_url(),
                    'author': unicode(page.document.author.profile),
                    'author_url': page.document.author.profile.get_absolute_url(),
                    'title': title,
                    'date': page.document.date_written.strftime("%Y %b %d"),
                    'page_count': page.document.documentpage_set.count(),
                    'larger': public_url(
                        get_thumbnail(page.image.path, "100").url
                    ),
                })

            img_name = "pagepicker%s.jpg" % i
            data_file_name = "pagepicker%s.json" % i

            proc = subprocess.Popen(["nice", "montage", 
                    "-background", "#FFFFFF",
                    "-tile", "{0}x1".format(len(page_images)),
                    "-geometry", "{0}x{1}+0+0".format(
                       thumb_size[0],
                       thumb_size[1],
                    )
                ] + page_images + [
                    os.path.join(dir_path, img_name)
                ])
            proc.communicate()
            with open(os.path.join(dir_path, data_file_name), 'w') as fh:
                json.dump({'data': page_data}, fh)

            manifest.append({
                'image': public_url(
                    "".join((settings.MEDIA_URL, os.path.join("pagepicker", img_name)))
                ),
                'image_size': thumb_size,
                'num_images': len(page_images),
                'datafile': public_url(
                    "".join((settings.MEDIA_URL, os.path.join("pagepicker", data_file_name)))
                ),
            })

        with open(os.path.join(dir_path, "manifest.json"), 'w') as fh:
            json.dump({'images': manifest}, fh)

        #os.system("rm -r %s" % tmpdir)
