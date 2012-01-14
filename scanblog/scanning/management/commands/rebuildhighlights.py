from django.core.management.base import BaseCommand

from scanning.tasks import update_document_images
from scanning.models import Document

class Command(BaseCommand):
    args = ''
    help = "Recreate the highlight images for all documents."

    def handle(self, *args, **kwargs):
        for doc in Document.objects.all():
            try:
                update_document_images(document=doc, process_pages=False)
            except Exception as e:
                print type(e), doc.pk

