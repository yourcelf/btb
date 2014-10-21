from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from annotations.models import Tag
from scanning.models import Document

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Denormalize the count of posts for each tag.

        # This could be done way more efficiently, but we have no reason to at
        # the moment.  It could be executed, for example, as a single SQL
        # query.
        tag_counts = defaultdict(int)
        for post in Document.objects.public().filter(type="post"):
            for tag in post.tags.all():
                tag_counts[tag.pk] += 1

        with transaction.atomic(): # Django 1.6
            for pk, count in tag_counts.iteritems():
                Tag.objects.filter(pk=pk).update(post_count=count)
