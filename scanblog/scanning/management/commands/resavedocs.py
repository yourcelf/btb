from django.core.management.base import BaseCommand

from scanning.models import Document

class Command(BaseCommand):
    args = ''
    help = "Re-save all documents.  Useful for correcting public/private permissions."

    def handle(self, *args, **kwargs):
        for d in Document.objects.all():
            d.save()
