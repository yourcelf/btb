import os

from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    args = ''
    help = "Set all permissions in the uploads directory for deploy."

    def handle(self, *args, **kwargs):
        for dirname in (os.path.join(settings.MEDIA_ROOT, settings.UPLOAD_TO),
                        os.path.join(settings.MEDIA_ROOT, "letters"),
                        os.path.join(settings.MEDIA_ROOT, "mailings"),
                        settings.PUBLIC_MEDIA_ROOT):
            print dirname
            os.system('sudo chown -R www-data.btb "%s"' % dirname)
            # files: -rw-rw-r--
            os.system('sudo chmod -R 0664 "%s"' % dirname)
            # directories: -rwxrwsr-x
            os.system('sudo find "%s" -type d -exec sudo chmod 2775 {} \\;' % dirname)
