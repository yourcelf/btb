import os

from django.core.management.base import BaseCommand
from django.conf import settings

from PIL import Image

class Command(BaseCommand):
    args = ''
    help = "Convert all Grayscale images in upload directory to RGB."

    def handle(self, *args, **kwargs):
        errors = []
        count = 0
        for root, dirs, files in os.walk(settings.MEDIA_ROOT, settings.UPLOAD_TO):
            for name in files:
                path = os.path.join(root, name)
                if path.endswith(".jpg"):
                    try:
                        img = Image.open(path)
                    except IOError:
                        errors.append(path)
                        continue
                    if img.mode == 'L':
                        img = img.convert('RGB')
                        img.save(path)
                        count += 1
        print "Converted", count, "images."
        if errors:
            print "The following images had errors:"
            for err in errors:
                print "  ", err
            response = raw_input("Delete them? (y/n) ")
            if response == "y":
                print "Deleting."
                for err in errors:
                    os.remove(err)
            else:
                print "Not deleted."

